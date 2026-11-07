# Survey Insight Assistant

**Turn hundreds of survey answers into clear themes, real quotes and recommendations in under a minute.**

[Try the live app](https://YOUR-APP-LINK.streamlit.app) · [See my portfolio](https://wong-jun-yi.netlify.app)

---

## The problem

Open-ended survey answers are often the most useful part of a survey, and the slowest to analyse. On my NTUC Starter Awards project, our team surveyed young workers about their first jobs and sorted every written answer into themes by hand. It took hours, and it was easy to miss patterns.

## What it does

1. **Upload a survey** as a CSV file, such as a Google Forms or Microsoft Forms export.
2. **See the numbers** straight away, with a chart for every multiple-choice and rating question.
3. **Get AI insights.** Google Gemini reads the written answers and returns:
   - 3 to 6 themes, with how many people fall into each
   - real quotes as evidence for every theme
   - a short summary and 3 practical recommendations
4. **Download a report** to paste into a presentation or document.

## How it works

- The app works out which questions are multiple choice, ratings or open-ended text.
- Charts are built with pandas and Altair.
- Open-ended answers are sent to Gemini with a structured prompt that asks for JSON, so the results always come back in the same shape and can be shown as cards.
- Each visitor gets 5 AI analyses per visit, so the free API quota can't be used up by one person.

## Built with

Python · Streamlit · pandas · Altair · Google Gemini API

## What I learnt

- **Start from a real problem.** Building a tool for a task I had done by hand made it easy to decide what mattered and what to leave out.
- **Prompting is product design.** Asking the AI for a fixed JSON structure made the output reliable enough to build a clean interface around.
- **Plan for real users.** Usage limits, clear error messages and keeping the API key out of the code were as important as the AI itself.

## Privacy

Survey data is only sent to Google Gemini when you click **Analyse with AI**. Nothing is stored by the app.

---

Made by **Wong Jun Yi**, IT student at Ngee Ann Polytechnic, focused on product management and AI automation.
[Portfolio](https://wong-jun-yi.netlify.app) · [LinkedIn](https://www.linkedin.com/in/jun-yi-wong-wjy)
