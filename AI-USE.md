# AI Use Declaration

**Course**: DHG 502 Digital Approaches in Historical Research
**Title**: Collocation analysis of "倭" in the *Ming Shi 明史*
**Name**: LAW Tsz-kin, Ken

**AI tools and models used**

GitHub Copilot Chat via Openrouter, GLM 5.3 Flash Model.

**Tasks for which AI was used**

- Install libraries, such as opencc, jieba, qhchina
- Convert traditional Chinese text to simplified Chinese
- Segmentated the text into sentences for analysis with no spaces and puncuations
- Collocation analysis & KWIC Analysis of target word "倭"
- Create userdict to extract historical names, locations, and titles relevant to the research question
- Create .png & .html based on analysis outcomes
- Create Python script of the workflow
- Assist in troubleshooting character-encoding issues and resolving Matplotlib font-fallback configurations

**Representative prompts / session excerpts**

- "Create a Python workflow to convert the 明史 text to simplified Chinese, split it into sentences on Chinese punctuation, and save one sentence per line in a data file."
- "Load a custom jieba dictionary with "倭" and related names/titles, then print 20 random segmented sentences that contain the target word for manual checking."
- "Use qhchina collocation analysis to compute collocates for 倭 with 5-word, 10-word, and sentence windows; filter p-values and save separate CSV reports."
- "Build an interactive HTML report in English with separate pages for the three methods and a final comparison page."
- "Use kwic on 王京 and 新 to show up to 10 passages in a 10-word window, and add卷/title information when available."
- "Generate summary PNG tables comparing the top 10 collocates by significance and strength."

**Important changes I made**

- Search for historical text source (*Ming Shi 明史* orginial text) and analysis tools (e.g. qhchina.helpers.texts.load_stopwords)
- Direct and verify that the generated dictionary integrated correctly and ensure proper historical terms were targeted
- Historical interpretation of the collocation and KWIC outputs
- Search for academic source for citation
- Design the study with topic, source, methods to use, indicators and statistical thresholds
- Redefine .png and .html layout style and data presentation
- Create README, report and AI-USE

**How I checked the output**

- Run analysis.py to regenerate data & outputs
- Review .csv titles and contents, make sure output use specific methods (e.g. 5-word) or use proper thresholds (e.g. p-value < 0.05)
- Open the .png & .html and check if the pages loaded & outputs presented correctly
- Manually check KWIC concordance lines against the original historical chapters
- Review the .csv ensure the results use the designed methods and statistical thresholds
