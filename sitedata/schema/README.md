# `sitedata` Schema README

The files in sitedata/ are generally produced by the tech team and then feed into the virtual website, which is managed by the web team.  Since this is a passage of data from one team to the other, in 2022 we decided to write out the schema expected by the web app.  These schema are purely for information purposes; they are not used in any formal schema validation process.

## Dependencies

In `paper_list.json`, the `session_id` **must map** to a `session_id` in `session_list.json`, and the `uid` for each time slot **must map** to a `uid` in the corresponding session in `session_list.json`.  

In `speakers.json`, the `session_id` **must map** to a `session_id` in `session_list.json`.