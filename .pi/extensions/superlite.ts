import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const BOOTSTRAP_MARKER = "superlite:using-superlite bootstrap for pi";

const extensionDir = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(extensionDir, "../..");
const skillsDir = resolve(packageRoot, "skills");
const bootstrapSkillPath = resolve(skillsDir, "using-superlite", "SKILL.md");
const agentsDir = resolve(packageRoot, "agents");

let cachedBootstrap: string | null | undefined;

export default function superlitePiExtension(pi: ExtensionAPI) {
	pi.on("resources_discover", async () => ({
		skillPaths: [skillsDir],
	}));

	pi.on("input", async (event, ctx) => {
		if (event.source !== "interactive" && event.source !== "rpc") return;
		await new Promise<void>((done) => {
			const child = spawn("bash", [resolve(packageRoot, "hooks/record-reply")], {
				cwd: ctx.cwd,
				stdio: ["pipe", "ignore", "ignore"],
			});
			child.once("error", () => done());
			child.once("close", () => done());
			child.stdin.on("error", () => {});
			child.stdin.end(JSON.stringify({ cwd: ctx.cwd, prompt: event.text }));
		});
	});

	// Pi transforms a copy for each model call. Keep the prefix stable across turns.
	pi.on("context", async (event) => {
		if (event.messages.some(messageContainsBootstrap)) return;

		const bootstrap = getBootstrapContent();
		if (!bootstrap) return;

		const bootstrapMessage = {
			role: "user" as const,
			content: [{ type: "text" as const, text: bootstrap }],
			timestamp: Date.now(),
		};

		const insertAt = firstNonCompactionSummaryIndex(event.messages);
		return {
			messages: [
				...event.messages.slice(0, insertAt),
				bootstrapMessage,
				...event.messages.slice(insertAt),
			],
		};
	});
}

function getBootstrapContent(): string | null {
	if (cachedBootstrap !== undefined) return cachedBootstrap;

	try {
		const skillContent = readFileSync(bootstrapSkillPath, "utf8");
		const body = stripFrontmatter(skillContent);
		cachedBootstrap = `${BOOTSTRAP_MARKER}

You have superlite. Its 'superlite:using-superlite' skill follows and is already loaded for this Pi session. Follow it now. Do not try to load using-superlite again.

${body}

${piToolMapping()}`;
		return cachedBootstrap;
	} catch {
		cachedBootstrap = null;
		return null;
	}
}

function stripFrontmatter(content: string): string {
	const match = content.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
	return (match ? match[1] : content).trim();
}

function piToolMapping(): string {
	return `## Pi tool mapping

For \`/superlite:start\` or another Superlite command, read the matching Markdown file in ${resolve(packageRoot, "commands")} and follow it with the current request as its arguments. For a human approval, end the turn and have the user send their approval as a normal chat message. A tool answer does not pass through the input hook. If Superlite redirects the run to another worktree, start a fresh Superlite session there before writing a review plan. Shell cd does not move this chat.

Pi has native skills but does not expose Claude Code's \`Skill\` tool. When a Superlite instruction says to invoke a skill, use Pi's native skill system instead: load the relevant \`SKILL.md\` with \`read\` when the skill applies, or let a human invoke \`/skill:name\` explicitly.

Pi's built-in coding tools are lowercase: \`read\`, \`write\`, \`edit\`, \`bash\`, plus optional \`grep\`, \`find\`, and \`ls\`. Use those for the corresponding actions: read a file, create or edit files, run shell commands, search file contents, find files by name, and list directories.

Pi does not ship a standard subagent tool and has no plugin agents. If a subagent tool such as \`subagent\` from \`pi-subagents\` is available, use it for Superlite's \`Agent\` dispatches: pass the full text of \`${agentsDir}/<name>.md\` (implementer, reviewer or test-runner, minus frontmatter) followed by the brief as the prompt, on the model tier that file names. Continue an earlier agent (\`SendMessage\`) with that tool's resume workflow. If no subagent tool is available, do the work in this session (the skills' inline mode) or explain the missing capability instead of inventing \`Agent\` calls.

Pi does not ship a standard task-list tool or \`AskUserQuestion\`. If an installed todo/task tool is available, use it. Otherwise track work in plan files or a repo-local \`TODO.md\`, and ask the user in plain text, batching up to 4 questions in one message.`;
}

function messageContainsBootstrap(message: unknown): boolean {
	const content = (message as { content?: unknown }).content;
	if (typeof content === "string") return content.includes(BOOTSTRAP_MARKER);
	if (!Array.isArray(content)) return false;
	return content.some((part) => {
		return (
			part &&
			typeof part === "object" &&
			(part as { type?: unknown }).type === "text" &&
			typeof (part as { text?: unknown }).text === "string" &&
			(part as { text: string }).text.includes(BOOTSTRAP_MARKER)
		);
	});
}

function firstNonCompactionSummaryIndex(messages: unknown[]): number {
	let index = 0;
	while ((messages[index] as { role?: unknown } | undefined)?.role === "compactionSummary") {
		index += 1;
	}
	return index;
}
