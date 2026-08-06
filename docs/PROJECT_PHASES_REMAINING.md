# Remaining work after Phase 34–38

The project now has:

- v0.1 Bubbles Gateway test package.
- Missing asset kit in native dimensions.
- Review queue and encoded draft asset bank.
- Gateway interaction payload.
- First LOG2 mini-route data package.
- Full route matrix for Super, GT, AF, LOG1 and LOG2.
- Save flag allocation plan.
- Content insertion order.
- Final QA/release plan.

## What still blocks a seamless playable experience

Only a few major engineering tasks remain, but they are the hardest tasks:

1. **Native menu/script hook** — make Bubbles/Gate Guide open the gateway menu in runtime.
2. **First route hook** — connect the LOG2 mini-route to actual map/NPC/item/battle scripts.
3. **Save integration** — write/read LOG4 flags safely without corrupting saves.
4. **Pixel cleanup** — convert the 55 character/enemy sheets from draft to approved pixel art.
5. **Full QA** — mGBA and hardware-like testing across route completion.

## Practical next milestone

The next milestone should be **v0.2 Gateway Runtime**:

- Talk to Bubbles.
- See a menu/list with Super, GT, AF, LOG1, LOG2.
- Select LOG2.
- Enter a safe placeholder map or existing fallback map.
- Return to gateway.

Once that works, the rest of the project becomes content expansion rather than core engine risk.
