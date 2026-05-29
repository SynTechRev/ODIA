"""Find ScriptManager + UpdatePanel IDs in Agenda page."""
import re

text = open("_questys_agenda_root.html", encoding="utf-8").read()

# Find form
m = re.search(r"<form[^>]*?action=[\"']([^\"']+)[\"']", text)
form_action = m.group(1) if m else None
m = re.search(r"<form[^>]*?id=[\"']([^\"']+)[\"']", text)
form_id = m.group(1) if m else None
m = re.search(r"<form[^>]*?name=[\"']([^\"']+)[\"']", text)
form_name = m.group(1) if m else None
print(f"form: action={form_action!r}  id={form_id!r}  name={form_name!r}")

# ScriptManager IDs
sm_ids = sorted(set(re.findall(r"id=[\"'](ctl00[^\"']*?ScriptManager[^\"']*)[\"']", text)))
print(f"\nScriptManager IDs: {sm_ids}")

# upXXX UpdatePanel IDs
ups = sorted(set(re.findall(r"id=[\"'](ctl00[\w_]*?up[A-Z][\w_]*)[\"']", text)))
print(f"\nUpdatePanel-like IDs: {len(ups)}")
for u in ups[:30]:
    print(f"  {u}")

# Hidden inputs around the calendar postback target
print("\nAll hidden inputs:")
for inp in re.findall(r"<input[^>]*?type=[\"']hidden[\"'][^>]*?>", text):
    name = re.search(r"name=[\"']([^\"']*)[\"']", inp)
    if name:
        print(f"  {name.group(1)}")

# Scan the calendar's containing element to see what UpdatePanel wraps it
print("\nCalendar's parent UpdatePanel:")
cal_pos = text.find('id="ctl00_DefaultContent_agendaCalendar"')
if cal_pos != -1:
    # Walk backward to find the enclosing UpdatePanel div
    before = text[:cal_pos]
    matches = list(re.finditer(r'<div[^>]*?id="([^"]*?(?:up|Update)[^"]*)"', before))
    if matches:
        last = matches[-1]
        print(f"  enclosing div id: {last.group(1)}  (pos {last.start()})")
