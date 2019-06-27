'''
    ANTLR Syntax in a JSON structure
    Copyright (C) 2019-2030  Ashok Hariharan, Bungeni Consulting

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import json, os, argparse, errno, re

parser = argparse.ArgumentParser()
parser.add_argument("--json", "-j", help="JSON File", required=True)


class JSONRule:

    def __init__(self, json_file):
        self.data = {}
        self.doc_rules = []
        self.valid_tree = {}
        self.data = self.load_json(json_file)

    def load_json(self, json_file):
        g4d = {}
        with open(json_file, encoding="utf-8", mode="r") as jsf:
            g4d = json.load(jsf)
        return g4d

    def add_doc_rule(self, rule):
        for doc_rule in self.doc_rules:
            if doc_rule["name"] == rule["name"]:
                return doc_rule
        self.doc_rules.append(rule)
        return rule

    def doc_rules_str(self):
        rules = []
        for doc_rule in self.doc_rules:
            rules.append('%s: %s ;' % ("{:<30}".format(doc_rule["name"]), "".join(doc_rule["rules"]) ))
        return "\n".join(rules)

    def root_rule(self):
        return self.data["root"]
    
    def all_rules(self):
        return self.data["rules"]

    def find_rule_by_name(self, rule_name):
        rules = self.data["rules"]
        for rule in rules:
            if rule["name"] == rule_name:
                return rule

        return None

    def rule_definition(self, rule_obj):
        '''
        Returns an array of rule definitions
        '''
        return rule_obj["definition"]
    
    def rule_set(self, rule_obj):
        # returns the set of the grouping type
        rule_defns = self.rule_definition(rule_obj)
        for rule_defn in rule_defns:
            if self.is_grouping(rule_defn):
                return rule_defn["set"]
        return None

    def rule_grouping_set(self, rule_grpng):
        return rule_grpng["set"]

    def rule_grouping_set_sorted(self, rule_grpng):

        rule_set = self.rule_grouping_set(rule_grpng)
        if "index" in rule_set[0]:
            return sorted(rule_set, key=lambda rule: rule["index"])
        else:
            return rule_set


    def is_grouping(self, defn_item):
        return "type" in defn_item and defn_item["type"] == "grouping"


    def rule_set_sorted(self, rule_obj):

        rule_set = self.rule_set(rule_obj)
        if "index" in rule_set[0]:
            return sorted(rule_set, key=lambda rule: rule["index"])
        else:
            return rule_set


    def rule_reference_as_string(self, rule_ref):
        rule_condition = rule_ref["condition"] if "condition" in rule_ref else ""
        rule_name = rule_ref["rule"]
        return rule_name + rule_condition

    def _dec_operator(self, operator):
        '''
        Decorates the operator with spaces around it
        '''
        return " " + operator + " "

    def render_rule_definition(self, set_item):
        '''
        Renders the rule definition for a rule, called by render_rule_syntax
        '''

        rules = []

        is_grouping = "type" in set_item and set_item["type"] == "grouping"
        
        if is_grouping:

            # get the grouping set
            set_item_operator = set_item["operator"] if "operator" in set_item else " "
            set_item_condition = set_item["condition"] if "condition" in set_item else ""
            
            set_item_set = set_item["set"]
            

            sub_rules = []

            for set_item in set_item_set:
                subs = " ".join(self.render_rule_definition(set_item))
                sub_rules.append(subs)
            
            if set_item_condition == "":
                rules.append(
                    set_item_operator.join(sub_rules)
                )
            else:
                rules.append(
                    " ( " + self._dec_operator(set_item_operator).join(sub_rules) + " )" + set_item_condition
                )
            
        else:
            rules.append(self.rule_reference_as_string(set_item))

        return rules


    def render_rule_syntax(self, rule_obj):
        '''
        Renders the complete ANTLR rule syntax for a rule
        '''
        
        name = rule_obj["name"]
    
        # get all the rule definitions
        # rule defintion can be a grouping or a diret reference to a rule
        rule_defns = self.rule_definition(rule_obj)

        full_rule = []
    
        for rule_defn in rule_defns:
            '''
            Rule definition can having groupings 
            groupings can have rules and other groupings
            '''
            full_rule.append("".join(self.render_rule_definition(rule_defn)))
        
        return "".join(full_rule)
        

    def validate_rule_set(self, rule_set):
        '''
        @rule_set
        Validates a set of rules referenced by a rule
        '''
        for item in rule_set:
            is_grouping = "type" in item and item["type"] == "grouping"
            if is_grouping:
        
                rule_grp_set = self.rule_grouping_set(item)
                validated = self.validate_rule_set(rule_grp_set)
                if not validated:
                    return validated
            else:
                ref_rule_name = item["rule"]
                if ref_rule_name[0].isupper():
                    continue
                else:
                    found = self.find_rule_by_name(ref_rule_name)
                    if found is None:
                        self.valid_tree[ref_rule_name] = "NOT_DEFINED"
                    else:
                        self.validate_rule(found)

    def validate_rule(self, the_rule):
        '''
        @the_rule: Rule Objec

        Checks if a rule is valid
        '''
        rule_set = self.rule_set_sorted(the_rule)
        self.validate_rule_set(rule_set)
 

    def validate_rules(self):
        '''
        Starting with the root rule, check if every referenced parser rule exists
        '''

        root = self.root_rule()
        
        the_rule = self.find_rule_by_name(root)
        self.validate_rule(the_rule)

        return self.valid_tree

    def build_all_rules(self):
        '''
        Reads the rules described in the JSON and renders its ANTLR syntax
        '''
        self.doc_rules = []
        for rule in self.all_rules():
            rule_syntax =  self.render_rule_syntax(rule)
            self.add_doc_rule(
                {"name": rule["name"], "rules": rule_syntax}
            )

def main(json_file):
    
    jrObj = JSONRule(json_file)
    jrObj.build_all_rules()
    print(" Rules in Antlr Syntax ")
    print(jrObj.doc_rules_str())
    print(" Validate Rule Tree ")
    print(jrObj.validate_rules())


 
if __name__ == '__main__':
    args = parser.parse_args()
    if args.json:
        main(
            args.json
        )
    else:
        parser.print_help()

