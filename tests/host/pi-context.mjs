import assert from "node:assert/strict";
import install from "../../.pi/extensions/superlite.ts";

const events = new Map();
install({ on: (name, callback) => events.set(name, callback) });
assert.ok((await events.get("resources_discover")()).skillPaths.length);
const context = events.get("context");
const user = { role: "user", content: "A build request", timestamp: 0 };
const summary = { role: "compactionSummary", summary: "Earlier turns", timestamp: 0 };
const first = await context({ messages: [user] });
assert.match(first.messages[0].content[0].text, /superlite:using-superlite bootstrap for pi/);
assert.equal(await context({ messages: first.messages }), undefined);
await events.get("agent_end")?.();
const second = await context({ messages: [user] });
assert.equal(second?.messages[0].content[0].text, first.messages[0].content[0].text);
assert.deepEqual((await context({ messages: [summary, user] })).messages[0], summary);

// An extension (including an agent tool) can enqueue a prompt but it cannot
// pass it through the approval recorder as interactive input.
assert.ok(events.has("input"));
assert.equal(await events.get("input")({source:"extension",text:"approve"}, {}), undefined);
