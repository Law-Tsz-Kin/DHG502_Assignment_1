# AI Use Declaration

**Course**: DHG 502 Digital Approaches in Historical Research
**Title**: Collocation analysis of "倭" in the *Ming Shi 明史*
**Name**: LAW Tsz-kin, Ken

**AI tools and models used**

GitHub Copilot Chat with Openrouter, GLM 5.3 Flash Model.

**Tasks for which AI was used**

Install libraries, such as opencc, jieba, qhchina
Convert *Ming Shi 明史* to simplified Chinese
Segmentate the *Ming Shi 明史* into sentences for analysis
Collocation analysis & KWIC Analysis of target word "倭"
Create .png & .html based on analysis outcomes
Create Python script of the workflow

**Representative prompts / session excerpts**

- "Create a Python workflow to convert the 明史 text to simplified Chinese, split it into sentences on Chinese punctuation, and save one sentence per line in a data file."
- "Load a custom jieba dictionary with 倭 and related names/titles, then print 20 random segmented sentences that contain the target word for manual checking."
- "Use qhchina collocation analysis to compute collocates for 倭 with 5-word, 10-word, and sentence windows; filter p-values and save separate CSV reports."
- "Build an interactive HTML report in English with separate pages for the three methods and a final comparison page."
- "Use kwic on 王京 and 新 to show up to 10 passages in a 10-word window, and add卷/title information when available."
- "Generate summary PNG tables comparing the top 10 collocates by significance and strength."

**Important changes I made**



**How I checked the output**
Run analysis.py to regenerate data & outputs
Review .csv titles and contents, make sure 
Open the .html and checked that the pages loaded correctly
