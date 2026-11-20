# Under the mango tree

Saanvi Mehra’s personal website. GitHub Pages serves the checked-in HTML from the root of `main`. The site uses local artwork and type, with no client-side content service.

Run `python3 build.py` to build from the published Markdown in `essays/` and `notebook/`. Open `index.html` directly for a preview. Run `./publish "Update the garden"` to build, commit, and push a website update.

The author’s Obsidian vault lives outside the repository. To import a complete public selection, run `python3 build.py --vault "/path/to/Mango notebook"`. The vault root must contain the `.mango-vault` marker. The builder mirrors Markdown from its `Tree/` folder only when the `publish` property is true. A new export withdraws previously exported notes absent from that selection. Keep a private vault outside this public checkout.

Each note has a stable lowercase `slug` for its page address. Optional fields are `title`, `date` (YYYY-MM or YYYY-MM-DD), `kind`, and `collection` (Found, Made, or both separated by a comma). An Obsidian wikilink links to the other published note.

Made lists Guthli and both essays together, newest first. Each entry in Made or Found has a reading page linked from the homepage. Photo and sound credits expand in the footer.

The complete introduction comes from the single public note with slug `saanvi-mehra`. Each fruit opens one piece. The fruit assignments are in `build.py`; their ink stems are in `assets/vine.js`.

Agents can start at `/llms.txt` and follow links to individual Markdown files. The index includes the bio and the full authored text of all published pieces.
