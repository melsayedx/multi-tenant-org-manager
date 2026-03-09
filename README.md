UTC vs local time
There's a concrete problem it prevents:

Local time is broken for databases because of DST (Daylight Saving Time). Twice a year, local time either jumps forward or repeats. During the "fall back" hour, two events that happened at different real moments can have identical local timestamps. Sorting by created_at produces wrong results. Querying "everything in the last 24 hours" crosses DST boundaries incorrectly.

UTC has no DST. It never repeats, never skips. 2026-03-09T14:32:00Z is one exact moment in time, globally unambiguous.

The standard rule in backend development: store UTC everywhere, convert to local only at the point of display (your frontend or API response, based on the user's timezone preference). The database never needs to know where the user is — that's a display concern, not a storage concern.