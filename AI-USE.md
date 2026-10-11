# AI Use Declaration

**Course**: DHG 502 Digital Approaches in Historical Research
**Title**: Collocation analysis of "倭" in the *Ming Shi 明史*
**Name**: LAW Tsz-kin, Ken

**AI tools and models used**

GitHub Copilot Chat with Openrouter, GLM 5.3 Flash Model.

**Tasks for which AI was used**

- Install libraries, such as opencc, jieba, qhchina
- Convert traditional Chinese text to simplified Chinese
- Segmentated the text into sentences for analysis
- Collocation analysis & KWIC Analysis of target word "倭"
- Create .png & .html based on analysis outcomes
- Create Python script of the workflow

**Representative prompts / session excerpts**

- "Create a Python workflow to convert the 明史 text to simplified Chinese, split it into sentences on Chinese punctuation, and save one sentence per line in a data file."
- "Load a custom jieba dictionary with "倭" and related names/titles, then print 20 random segmented sentences that contain the target word for manual checking."
- "Use qhchina collocation analysis to compute collocates for 倭 with 5-word, 10-word, and sentence windows; filter p-values and save separate CSV reports."
- "Build an interactive HTML report in English with separate pages for the three methods and a final comparison page."
- "Use kwic on 王京 and 新 to show up to 10 passages in a 10-word window, and add卷/title information when available."
- "Generate summary PNG tables comparing the top 10 collocates by significance and strength."

**Important changes I made**

- Use template from qhchina.analytics.collocations.find_collocates for collocation analysis
- Use tmplepalte from qhchina.helpers.texts.load_stopwords for stopwords filter
- Create requirements.txt for document all the dependencies
- Create userdict.txt for "倭" and related names, titles, and terms relevant to the target word for manual checking
- Create index.csv as master lookup table link exact quotation with the belonging chapter

**How I checked the output**
- Run analysis.py to regenerate data & outputs
- Review .csv titles and contents, make sure output use specific methods (e.g. 5-word) or use proper conditions (e.g. p-value < 0.05)
- Open the .png & .html and check if the pages loaded & outputs presented correctly
