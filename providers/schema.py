# providers/schema_small.py
RECIPE_SCHEMA = {
  "name": "r",
  "schema": {
    "type": "object", "additionalProperties": False,
    "properties": {
      "r": {
        "type": "array", "minItems": 5, "maxItems": 5,
        "items": {
          "type": "object", "additionalProperties": False,
          "properties": {
            "t": {"type":"string"},
            "tm":{"type":"integer","minimum":20,"maximum":30},
            "m": {"type":"string"},
            "sv":{"type":"integer","minimum":1,"maximum":10},
            "st":{"type":"array","minItems":4,"maxItems":5,"items":{"type":"string"}}
          },
          "required": ["t","tm","m","sv","st"]
        }
      }
    },
    "required": ["r"]
  },
  "strict": True
}

