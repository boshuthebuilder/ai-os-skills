# Signs of AI writing. Detailed reference.

The authoritative pattern list for the `ai-writing-audit` skill. **Synced 2026-08-15** against the
Wikipedia essay revision recorded in [`tools/coverage.json`](tools/coverage.json); run
`python3 tools/sync_check.py` to verify the essay has not moved on (see *Provenance* at the end).

Primary sources, weighted over SEO content: the Wikipedia essay
[Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (which era-tags its
own vocabulary, grades evidence by strength, and lists what does *not* indicate AI); the
[tropes.fyi](https://tropes.fyi/directory) catalogue (regex-validated against verified human and AI
corpora, Feb 2026); a peer-reviewed stylometry study in
[Nature HSSC 2025](https://www.nature.com/articles/s41599-025-05986-3); the excess-vocabulary corpus
study in [Science Advances 2025](https://www.science.org/doi/10.1126/sciadv.adt3813); the ACL 2025
lexical-overrepresentation study
["Why Does ChatGPT 'Delve' So Much?"](https://aclanthology.org/2025.coling-main.426.pdf); Pangram
Labs' [detection guide](https://www.pangram.com/blog/comprehensive-guide-to-spotting-ai-writing-patterns);
lab statements on em-dash suppression
([TechCrunch, Nov 2025](https://techcrunch.com/2025/11/14/openai-says-its-fixed-chatgpts-em-dash-problem/))
and negative parallelism
([TechCrunch, Apr 2026](https://techcrunch.com/2026/04/20/ai-writing-its-not-just-this-its-that-barrons/)).

## How to read this list

Models are trained to pick the likely next token, so their prose regresses to the centre of the training
distribution. The patterns below are the footprints of that regression. Two things changed since the
2023–2024 word-list era, and they set how you must weigh a hit:

1. **The loud lexical tells get patched.** Once a word or a punctuation habit becomes notorious, labs train
   or instruct it away. "delve" dropped off sharply in frontier chat models through 2025; OpenAI shipped a
   working em-dash-suppression instruction in November 2025. A single banned word is therefore weak and
   perishable evidence.
2. **Structure outlasts vocabulary.** What a model cannot cheaply hide is the *shape* of its output:
   uniform sentence rhythm, stacked patterns, and literal tool markup it leaked into the text. These are the
   durable signals.

So grade every hit into one of three bands and judge the document on **cluster density**, not any single
match. Wikipedia's own essay made the same move: single word or phrase hits are "weak" evidence; clusters
and hard artifacts are "strong".

- **Band 1 — near-decisive.** Leaked citation/tool markup (§1); very low sentence-length variance (§2);
  chat-mode leakage (§3).
- **Band 2 — fires in clusters.** §4–§15. One is ordinary; three-plus stacked in a short span is the tell.
- **Band 3 — contributory only.** §16–§20. Count toward a cluster, never conclude from alone.

---

## Band 1 — near-decisive

### 1. Citation and markup artifacts

The strongest signal in the whole catalogue, and the newest. When text is pasted out of a chat product, the
rendering tokens sometimes come with it. These are machine artifacts, not style: **one is enough** to
conclude the passage was generated. Search for, and delete, the leaked markers below, then verify the claim
each was attached to (the citation it "supported" may be fabricated).

| Product | Leaked tokens |
|---|---|
| ChatGPT | `oaicite`, `oai_citation`, `contentReference`, `:contentReference[oaicite:...]`, `attributableIndex`, `turn0search0`, `turn0view0`, `turn0news0` |
| Gemini | `[cite: 1]`, `[cite_start]`, `[span_1]`, `[start_span]` |
| Grok | `grok_card`, `grok_render_citation_card_json` |
| DeepSeek | lenticular brackets with digits and a dagger, e.g. `【85†L261-269】` |
| Perplexity | `ppl-ai-file-upload`, `attached_file` |
| Unclassified | `:::writing{variant="document" id="12345"}`, often paired with a bare `:::` at the end |

### 2. Sentence-length rhythm (burstiness)

The strongest *stylistic* tell, and the one that has gained the most evidence since 2024. Human writing
varies sentence length a lot; LLM writing clusters near a single length, often with a comma in the middle.
Quantified: human academic prose runs a sentence-length standard deviation of roughly 8.2 words, against
about 4.1 for GPT-4o and 5.3 for Claude (Nature HSSC 2025). Low "burstiness" is what detectors like GPTZero
lean on precisely because it is expensive to fake.

Fix by varying length deliberately. Put a three-word sentence next to a thirty-word one. Use the occasional
fragment. Read the passage aloud; if it plods in a steady beat, restructure.

### 3. Chat-mode leakage

The assistant's own voice left inside a document. Like §1, this is provenance rather than style — the text
around it was pasted from a chat session — so treat one confirmed hit as near-decisive, after checking it is
not quoted or deliberately meta text. Four families:

a. **Knowledge-cutoff and source-availability disclaimers.** The old form names the training cutoff ("as of
   my last knowledge update"); the current form disclaims the *sources* ("specific details are not widely
   documented", "based on available information", "limited in the provided search results") and then
   speculates anyway — including the "maintains a low profile" dodge for missing personal details. The
   speculation that follows is exactly as unfounded as the disclaimer admits.

b. **Direct address to the operator.** "I hope this helps", "Would you like me to...", "let me know",
   "is there anything else", "here is a detailed breakdown". Genre matters: in an email or letter these
   phrases are ordinary human correspondence — the tell is assistant-to-operator talk inside a document
   that addresses no one, so judge against what the document is.

c. **AI self-disclosure and refusal residue.** "As an AI language model...", "I cannot fulfil this
   request". The essay tags these historical (2023–2024 chatbots), but when one does appear it is still
   decisive.

d. **Placeholder text the operator forgot to fill.** "[Insert X here]", "[Your Name]", "(Add your channel
   URL here)", "This section needs expansion", placeholder dates like `2025-xx-xx`, and pasted prewriting
   or submission advice ("Delete this section before submission").

These are not rewritten — delete them and re-verify the claims they sat next to.

---

## Band 2 — fires in clusters

### 4. Negative parallelism

Now the single most commonly identified tell (its use in corporate communications roughly quadrupled from
2023 to 2025, and it is named as a tic of 2025-era frontier models). Forms: "It's not X, it's Y", "Not only
X, but Y", "Not just X, but also Y", and the reversed "X rather than Y" — the last particularly common in
Grok output, and judged by density, since a lone "rather than" is ordinary English.

| AI-shaped | Human-shaped |
|---|---|
| It is not a product. It is a movement. | It is more of a movement than a product. |
| Not only is it fast, but it is also cheap. | It is fast and cheap. |
| This is not just an update. It is a rethink. | This is a rethink, not just an update. |
| A fluid coalition rather than a fixed state. | A fluid coalition. (Or name what it actually was.) |

### 5. Formatting overkill

Consistently cited across every current source. Four sub-patterns:

a. **Bold on most lines.** Bold stops meaning anything when everything is bold. Reserve it for headings,
   table headers, and the occasional load-bearing term.

b. **Bulleted list whose bold title the next sentence restates.** Pick one.

> - **Add to Meta Business Portfolio.** Adding to the Meta Business Portfolio covers Facebook Page and
>   Instagram. → **Add to Meta Business Portfolio.** Covers Facebook Page and Instagram.

c. **Unicode decoration.** Arrows (→), decorative bullets, and emoji section headers used as ornament.

d. **The document restates its own title as a heading.** A model does not see the title bar above the text
   it is asked for, so it writes one — a top-level heading repeating the document or article name before
   the content starts.

### 6. Document mechanics

Structural habits of chat output, most visible in Markdown documents. Individually weak, but they travel
together, so judge them as one pattern:

- **Title Case Headings** where the house style is sentence case.
- **Skipped heading levels** — sections start at `###` with no `##` above them.
- **More than one top-level heading** — a Markdown-to-document translation artifact.
- **Headings that contain only other headings**, with no text of their own between the levels.
- **Thematic breaks (`---`) between sections**, used as decoration rather than meaning.
- **Tables where prose belongs** — small gratuitous tables, or near-empty ones, that a person would have
  written as a sentence.

Fix by re-outlining: sentence-case the headings, restore the level ladder, delete the decorative rules, and
turn hollow tables back into prose.

### 7. Rule of three (triplets)

Three-item lists everywhere: adjectives, benefits, takeaways. Models default to three because it is rhythmic
and over-represented in marketing prose.

| AI-shaped | Human-shaped |
|---|---|
| Innovative, transformative, and groundbreaking. | (Pick one. Or use two, or four if the content needs four.) |
| Convenient, efficient, scalable. | Convenient and efficient. |

Triplets are legitimate in brand bios, taglines, and creative writing. The tell is when they stack across
paragraphs and the third item is filler. tropes.fyi catalogues the same thing as "Tricolon Abuse".

### 8. Compulsive summaries and outline-like conclusions

"In conclusion", "Overall,", "To summarise", "In summary" on short sections that needed no summary. The
instinct comes from academic and corporate training data. tropes.fyi flags the escalation, "Fractal
Summaries", where the same wrap-up recurs at every heading level, not just the end.

The document-level form is the formulaic closer: "Despite [praise], [subject] faces several challenges...",
"Despite these challenges...", and sections titled "Future Outlook", "Future Prospects" or "Challenges and
Legacy" — a rigid challenges-then-vague-optimism outline bolted onto the end. The tell is the formula, not
any mention of a challenge. Fix by ending on the last substantive point.

### 9. Trailing "-ing" analysis

Sentences ending in a present-participle phrase that adds vague commentary or attribution: "highlighting",
"underscoring", "reflecting", "ensuring", "fostering", "contributing to". Named in the Wikipedia essay as a
current pattern (its "superficial analyses"). Search-connected models now attach the same empty gloss to a
*named* source — "Ebert highlighted the lasting influence" — regardless of whether the source says anything
close, so verify the attribution, not just the grammar.

| AI-shaped | Human-shaped |
|---|---|
| Sales rose 12%, reflecting strong consumer demand. | Sales rose 12%. Consumer demand was strong. |
| She joined in 2019, bringing experience from two startups. | She joined in 2019. She came from two startups. |

### 10. False ranges

"From X to Y" implying a spectrum that is not in the source. Acceptable for a real, verifiable continuum
("from £5 to £500"); not for vague pseudo-ranges that gesture at scale ("from intimate gatherings to global
movements").

### 11. Sycophancy and collaborative framing

A behavioural tell, distinct from the lexical flattery in §19. Labs tuned models warmer through 2025–2026,
and one 2026 study found the major chat assistants agree with a user about 49% more often than a person
would. The visible residue is the praise-first opener and the reflexive validation: "Great question",
"You're absolutely right", "Certainly!", "Of course!", "I'd be happy to" — and the pedagogical "we" that
frames a document as a guided tour: "Let's break this down", "let's explore", "we will examine", "as we can
see". Delete them and state the point directly. tropes.fyi adds sibling tics: "Here's the Kicker", "The
Truth Is Simple", "Think of It As".

### 12. Copulative avoidance

Dodging the plain "is"/"are"/"has": "serves as", "stands as", "marks", "functions as", "operates as",
"represents", and the marketing verbs "boasts", "features", "offers", "maintains" where "has" belongs — plus
the lead-sentence "refers to" that defines the term instead of the thing. One corpus study measured an over
10% drop in "is"/"are" in post-2023 academic writing, and AI copyedits "improve" text in exactly this way.
Recent output dodges more elaborately: "ventured into politics as a candidate" for "was a candidate". Judge
by density — one "serves as" is English; five copula dodges on a page is the tell. Do not count auxiliary
uses ("has been featured"). Fix by restoring the plain verb.

### 13. Vague attributions (weasel wording)

Claims attributed to an authority that is never named, and source quantities quietly exaggerated: "experts
argue", "observers have cited", "some critics argue", "industry reports", "described in scholarship",
"researchers and conservationists", "widely regarded as", "several publications" when one is cited, and
"such as" lists implying more examples than the sources contain. LLMs present one or two sources as a
consensus. Fix by naming the source or dropping the claim.

### 14. Significance inflation and canned notability

Puffing up importance with a distinct, recyclable repertoire: "stands/serves as a testament", "a pivotal
moment", "underscores its significance", "reflects broader trends", "setting the stage for", "marking a key
turning point", "evolving landscape", "focal point", "indelible mark", "deeply rooted", "enduring legacy",
"cements its", "continues to captivate" — applied to any subject, however mundane, sometimes right after
conceding the subject is minor. Related habits: situating everything amid broader "debates"; year-by-year
career narration; "best known for" on subjects nobody knows; a boilerplate "Awards and recognition"
section whether or not there are awards; and — in 2025+ models — hammering notability by listing coverage
instead of substance ("independent coverage", "trade publications", "profiled in", "maintains an active
social media presence"). For species and places, the same reflex over-emphasises
ecosystem connections and conservation efforts that no source records. Fix by replacing the verdict with
the fact that earned it — or deleting the sentence, which usually loses nothing.

### 15. Elegant variation (synonym cycling)

Repetition-penalty residue: the text will not reuse a plain noun, so "the artists" become "the non-conformist
artists", "the like-minded artists", "the Russian avant-garde artists" in consecutive sentences, each entity
wearing a new costume every time it appears. Invisible to a regex — read for it. Two caveats: writers taught
to avoid repetition (common outside English-speaking schooling) do this naturally, and separately-generated
passages pasted together will not show it. Fix by repeating the plain noun; repetition is how readers track
who is who.

---

## Band 3 — contributory only

Never conclude from these alone. Each counts toward a cluster.

### 16. Vocabulary (era-tagged)

The word-list is the most perishable layer. The essay tiers it by model generation rather than keeping one
flat list, because the words rotate as models are retuned. Treat a word as *weak* evidence, check the era
before flagging, and take the list literally: an overused word does not implicate its synonyms, and context
matters ("underscore" can be a literal mark; "landscape" can be land).

- **2023–mid-2024 (GPT-4 era), now fading:** additionally (sentence-initial), boasts, bolstered, crucial,
  delve, emphasizing, enduring, garner, intricate/intricacies, interplay, key (adjective), landscape
  (abstract), meticulous/meticulously, pivotal, tapestry (abstract), testament, underscore (verb),
  valuable, vibrant. "delve" in particular dropped off sharply in 2025 frontier output; lower-quality
  "signs of AI" blogs still lead with it.
- **mid-2024–mid-2025 (GPT-4o era):** align with, bolstered, crucial, emphasizing, enduring, enhance,
  fostering, highlighting, pivotal, showcasing, underscore, vibrant.
- **mid-2025+ (GPT-5 era):** emphasizing, enhance, highlighting, showcasing — plus the canned-notability
  phrasing of §14.
- **Grok:** superficially "scientific" words — causal, empirical, correlate — and a persistent
  "underscore" as of 2026.
- **Still overused but often legitimate:** critical, comprehensive, deep dive, elevate, ensure, leverage
  (verb), myriad, navigate (metaphor), plethora, realm, robust, seamless.

A note on folklore: the popular story that "delve" entered LLMs through a specific dialect of RLHF
annotators is **not established** — a corpus study found no such dialect signal and left the cause open. Do
not repeat it as fact.

### 17. Hedging clichés

"It is important to note that", "It is worth noting that", "Notably,", "Importantly,", "It should be
acknowledged that". If the note matters, state it. If it does not, cut it. The essay files the didactic
form ("it's important to remember...", safety advice to an imagined reader, "may vary") under its
*historical* indicators — a 2023-era chatbot habit now rare — so weight recent text accordingly.

### 18. Stock transitions

"Furthermore,", "Moreover,", "Additionally,", "On the other hand,", "That being said,", "With that said,".
Not wrong, but stacked they read as AI. Prefer "And", "But", "Also", or drop the transition. The essay is
explicit that transition words *in isolation* are an ineffective indicator — count them only inside a
cluster.

### 19. Flattery and puffery

Praise the content has not earned: fascinating, intriguing, remarkable, exceptional, captivating,
mesmerising, transformative, paradigm-shifting, powerful (with no specific power), compelling, must-read —
and the travel-brochure register: "vibrant", "rich heritage", "nestled", "in the heart of", "natural
beauty", "renowned", "groundbreaking", "diverse array", "commitment to". Older models (GPT-4) were blatant;
newer ones are subtly positive and avoid outright superlatives, so the lexical form is weakening — the
behavioural form is §11. If removing the adjective loses no information, remove it.

### 20. Punctuation habits

- **Em-dash density.** Once called "the most infamous tell", now demoted and contested: it is gameable
  (OpenAI ships a suppression setting) and publicly defended as ordinary punctuation. Judge **density**,
  not presence: a natural writer uses two or three em-dashes in a piece; LLM output can run twenty-plus.
  Flag only above roughly one per hundred words, always as a contributor. Watch for the double hyphen
  (`word--word`) as the replacement once a writer or model starts avoiding the literal character.
- **Curly quotes in source files.** ChatGPT (mid-2025+) and DeepSeek emit curly quotation marks and
  apostrophes; Gemini and Claude typically do not. In a Markdown or code file authored in a plain editor,
  curly marks hint at paste-from-chat — but word processors, macOS/iOS defaults, and grammar tools curl
  quotes too, so this is weak evidence at best.

---

## Model fingerprints

When the source model matters, these tendencies are documented well enough to help attribute (all as of
2026, all soft signals):

- **ChatGPT** — most detectable overall; most likely to leak the §1 citation artifacts; curly quotes from
  mid-2025. Likely the most widely used, so the default suspect.
- **Gemini** — flagged more on rigid hierarchical structure than on vocabulary; more concise than ChatGPT;
  straight quotes.
- **Grok** — pseudo-scientific vocabulary ("causal", "empirical", "correlate"), a persistent "underscore",
  the "X rather than Y" reversal, and a ChatGPT-like taste for broader-context framing (§14).
- **Claude** — the best sentence-length variance (hardest to catch on §2) and relatively concise, with a
  documented residual tendency to over-hedge and moralise as a side effect of sycophancy reduction.

## Scoring: how the scanner and you should decide

`tools/audit.py` groups hits by band and prints a verdict on the same logic you should apply by hand:

- Any **Band 1** hit → conclude AI-shaped (verify markup is a leaked token, not a code sample, and that
  chat-mode leakage is not quoted or meta text).
- No Band 1, but **three or more distinct Band 2 patterns** clustered → AI-shaped. The §6 mechanics count
  as one pattern no matter how many sub-checks fire.
- Only **Band 3** hits → inconclusive; a human wrote "crucial" too. Read for rhythm before judging.

Reduce density across bands. Do not chase zero on any single pattern. When you know the author's earlier
writing, a pronounced, sudden shift in register, formatting, or vocabulary counts toward the cluster too —
it is the change that signals, not any single feature of the new text.

## Calibration: what not to flag

The essay keeps a list of ineffective indicators, and it doubles as a false-positive guard for this skill.
None of the following is evidence of AI authorship:

- **Perfect grammar, or "fancy"/formal prose.** Skilled writers exist; the overuse correlation attaches to
  *specific words*, not to formality in general.
- **Mixed registers** (clinical plus emotional, casual plus formal) — often a technical person writing
  casually, youth, playfulness, or several authors on one document.
- **A "bland" or "robotic" feel** on its own — name the actual pattern or drop the accusation.
- **Transition words, a lone em-dash, curly quotes, or one "delve"** in isolation — contributors only.
- **National spelling variants or typos** — humans, not models.

And the strongest signs a text is *human*: it predates November 2022; the author can explain their editorial
choices when asked; and the syntax is irregular — varied constructions, small grammatical quirks, real typos.
Detection by style alone is genuinely hard (untrained readers perform near chance; only heavy LLM users
reliably beat it), so when the bands do not stack, say "inconclusive", not "AI".

## Limits of automated scanning

The scanner finds the easy cases. It cannot judge sentence rhythm (§2 — the strongest stylistic signal, and
essentially invisible to regex), elegant variation (§15), whether a triplet is brand voice, whether
"navigate" is literal or metaphor, whether a bullet title is load-bearing, or whether an attribution is
earned. Always read the document yourself after the scan. The scanner is triage, not a verdict.

## Brand-voice exception

Phrases from a brand's voice guide, a bio bank, or a real human author are not to be edited just because
they pattern-match. The job is to remove tells that came from the model, not to flatten a person's writing.
When in doubt, ask which phrases are intentional.

## Provenance

This catalogue is synced to the Wikipedia essay deterministically. The essay revision it was last verified
against, and the mapping from every essay section to a section here (or to a recorded exclusion — wikitext,
citation-forensics and Wikipedia-process signs are out of scope for general prose), live in
[`tools/coverage.json`](tools/coverage.json). `python3 tools/sync_check.py` re-fetches the live essay and
fails loudly if it has sections this catalogue does not account for, or if its vocabulary lists have
changed since the last sync. The vocabulary layer (§16) is the most perishable part of this file; the
structural signals age far more slowly.
