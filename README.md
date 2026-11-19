# Under the mango tree

Saanvi Mehra’s personal website. GitHub Pages serves the checked-in HTML from the root of `main`. The site uses local artwork and type, with no client-side content service.

Run `python3 build.py` to build from the published Markdown in `essays/` and `notebook/`. Open `index.html` directly for a preview. Run `./publish "Update the garden"` to build, commit, and push a website update.

The author’s Obsidian vault lives outside the repository. To import a complete public selection, run `python3 build.py --vault "/path/to/Mango notebook"`. The vault root must contain the `.mango-vault` marker. The builder mirrors Markdown from its `Tree/` folder only when the `publish` property is true. A new export withdraws previously exported notes absent from that selection. Keep a private vault outside this public checkout.

Each note has a stable lowercase `slug` and a `branch` of Reading, Writing, Hinduism, Work, Roots, or Music. Optional fields are `title`, `date` (YYYY-MM or YYYY-MM-DD), and `kind`. The renderer supports paragraphs, headings, lists, blockquotes, rules, emphasis, web links, and Obsidian links with optional aliases. Links between notes use the public title or slug. The same links generate both backlinks and the interactive neighbourhood graph.

The native essay retains its historical route at `writing/stanford-essays.html`. Nyght Serif sets the headings and quotations. Onest sets the body and interface. Both families are served locally with their licences in `assets/`.
