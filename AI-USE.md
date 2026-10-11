# AI Use Declaration

**Course:** DHG 502 Digital Approaches in Historical Research
**Assignment:** Collocation analysis of 倭 in the *Ming Shi* 明史
**Date:** 2026-10-11

## AI tools and models used

I used GitHub Copilot in VS Code as the AI assistance for this assignment. The session used the IDE-integrated Copilot agent with the configured model available for the project at the time of work, which was the Z.ai GLM model exposed through GitHub Copilot. No other AI tool or model was used for the analysis itself.

## Tasks for which AI was used

1. Environment and dependency setup
   - Helped define the required Python packages and version constraints for the project.
   - Confirmed the appropriate libraries for OpenCC, jieba, qhchina, pandas, and report generation.

2. Corpus inspection and preprocessing design
   - Helped identify the structure of the *Ming Shi* text, including volume headings, punctuation patterns, citation markers, and chapter delimiters.
   - Advised on how to normalize the text, split sentences, strip noise, and maintain volume/index references.

3. Script implementation and debugging
   - Drafted and refined `analysis.py` to perform data preparation, custom dictionary loading, tokenization, collocation analysis, and report generation.
   - Helped troubleshoot issues in segmentation, output naming, filtering, and HTML/table generation.

4. Output validation and reporting
   - Suggested the checks needed to verify that collocate outputs were correct and that the HTML pages and summary tables rendered as intended.
   - Assisted in checking deterministic regeneration of files from the source text.

## Representative prompts / session excerpts

The following are representative requests and prompts used in the session:

- "Create a Python workflow to convert the 明史 text to simplified Chinese, split it into sentences on Chinese punctuation, and save one sentence per line in a data file."
- "Load a custom jieba dictionary with 倭 and related names/titles, then print 20 random segmented sentences that contain the target word for manual checking."
- "Use qhchina collocation analysis to compute collocates for 倭 with 5-word, 10-word, and sentence windows; filter p-values and save separate CSV reports."
- "Build an interactive HTML report in English with separate pages for the three methods and a final comparison page."
- "Use kwic on 王京 and 新 to show up to 10 passages in a 10-word window, and add卷/title information when available."
- "Generate summary PNG tables comparing the top 10 collocates by significance and strength."

These prompts were then refined iteratively based on the script output and the data itself.

## Important changes I made

The project was substantially built around the AI-generated analysis workflow:

- Created the preprocessing pipeline in `analysis.py` to convert the source text to simplified Chinese, split sentences, remove punctuation and citation markers, and add per-line volume/index metadata.
- Built the custom word list in `data/userdict.txt` for 倭 and related names, official titles, and near-synonym terms relevant to the research question.
- Implemented collocation analysis using `qhchina.analytics.collocations.find_collocates` with the required windows and measures: log-likelihood, logDice, and FDR-adjusted p-values.
- Saved the per-method CSV files in `output/` and generated the interactive HTML summary and KWIC pages.
- Produced the PNG comparison tables for significance vs. strength and cross-method ranking.
- Updated `AI-USE.md` and `requirements.txt` so the workflow, dependencies, and AI use are documented in a reproducible way.

## How I checked the output

I verified the outputs by running the analysis script directly and then inspecting the generated artifacts:

- Ran `python analysis.py` to regenerate the data, collocation outputs, and reports from the source text.
- Confirmed that the generated CSVs existed in `output/` and that the rows matched the expected filtering logic (adjusted p-value < 0.05, logDice ranking, and method-specific output names).
- Opened the HTML reports and checked that the pages loaded correctly, that the tables were sortable, and that the comparison page included the required indicators.
- Inspected the KWIC output for the selected collocates (王京 and 新) to ensure the passages were correctly bounded to a 10-word window and included the卷/title information when present.
- Reviewed the summary PNGs to ensure they reflected the top-10 collocate rankings and the method comparison.
- Re-ran the script after adjustments to confirm the results were deterministic and that no broken paths or formatting issues remained.

## Summary

AI assistance was used to accelerate corpus preparation, script construction, validation, and reporting. The analysis was ultimately checked by executing the code and verifying the generated outputs against the assignment requirements. No AI tool beyond GitHub Copilot in VS Code was used for this project.