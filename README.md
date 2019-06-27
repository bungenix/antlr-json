# antlr-json-serialization

A JSON serialization of ANTLR rules, a more evolved version of this is used by the [BungeniX Text to XML Parser](https://www.bungeni.com/text_to_akomantoso.html)



For a set of ANTLR rules like this:

```
doc                           :  ( preface   preamble   body   conclusion )+ ;
preface                       : preface_start preface_sentences ;
preface_start                 : PREFACE_START ;
preface_sentences             : sentence+ ;
preamble                      : preamble_start?  ( preamble_lines | recitals | blah )+ ;
preamble_start                : PREAMBLE_START ;
preamble_lines                : preamble_line+ ;
preamble_line                 : sentence ;
sentence                      : SENTENCE+ NEWLINE+ ;
recitals                      : recital+ ;
recital                       : recital_start recital_lines ;
body                          : book ;
book                          : sentence+ ;
conclusion                    : sentence ;
```

It provides a semantic JSON syntax to represent the same, for e.g the following is a JSON expression of the `doc` parser rule:

```
    {
        "name": "doc",
        "definition": [{
            "type": "grouping",
            "condition": "+",
            "set": [
                {
                    "index": 1,
                    "rule": "preface"
                },
                {
                    "index": 2,
                    "rule": "preamble"
                },
                {
                    "index": 3,
                    "rule": "body"
                },
                {
                    "index": 4,
                    "rule": "conclusion"
                }
            ]
        }]
    },

```
and more complex nested rule structures:

```
    {
        "name": "preamble",
        "definition": [ 
            {
            "type": "grouping",
            "comment": "preamble_start? (preamble_lines|recitals)+",
            "set": [
                {
                "rule": "preamble_start",
                "index": 1,
                "condition": "?",
                "comment": "preamble_start?"
                },
                {
                    "type": "grouping",
                    "index": 2,
                    "condition": "+",
                    "operator": "|",
                    "comment" : "(preamble_lines|recitals)+",
                    "set": [
                        {
                            "rule": "preamble_lines",
                            "index": 1
                        },
                        {
                            "rule": "recitals",
                            "index": 2
                        },
                        {
                            "rule": "blah",
                            "index": 3
                        }                       
                    ]
                }
            ]
        }
        ]
    },
```

the `doc_rules_str` api returns all the Rules in ANTLR syntax. You will need to call `build_all_rules` to generate the rules from JSON.