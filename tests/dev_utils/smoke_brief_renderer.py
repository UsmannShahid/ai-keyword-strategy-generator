from brief_renderer import brief_to_markdown
brief = {
  "title":"Best Sofas for Small Houses",
  "meta_description":"Compact, comfy options.",
  "outline":{"H2":["Intro", {"H3":["Tip A","Tip B"]}, "Conclusion"]},
  "related_keywords":["compact sofas","loveseats"],
  "suggested_word_count":1200,
  "content_type":"listicle",
  "internal_link_ideas":["/small-space-decor"],
  "external_link_ideas":["https://example.com/guide"],
  "faqs":[{"question":"Are loveseats good for small rooms?","answer":"Yes."}]
}
md = brief_to_markdown(brief)
print(md[:400] + "\n...\nOK")
