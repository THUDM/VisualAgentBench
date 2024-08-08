import os
import json
import cssutils
from bs4 import BeautifulSoup

from .screenshot import take_screenshot

cssutils.log.setLevel(10000)

def parse_css(css):
    parser = cssutils.CSSParser()
    stylesheet = parser.parseString(css)
    rules = {}
    for rule in stylesheet.cssRules:
        if rule.type == rule.STYLE_RULE:
            selector = rule.selectorText.strip()
            styles = rule.style.cssText.strip()
            rules[selector] = styles
    return rules

def matches_simple_selector(element, selector):
    if selector.startswith('#'):
        id_ = selector[1:]
        if element.get('id') != id_:
            return False
    elif selector.startswith('.'):
        classes = selector[1:].split('.')
        for cls in classes:
            if cls not in element.get('class', []):
                return False
    else:
        parts = selector.split('.')
        tag = parts[0] if parts[0] else None
        if '[' in tag:
            tag = tag[:tag.find('[')]
        classes = parts[1:]
        if tag and tag != element.name:
            return False
        for cls in classes:
            if cls not in element.get('class', []):
                return False
        if '[' in selector and ']' in selector:
            attr = selector[selector.find('[') + 1:selector.find(']')].split('=')
            attr_name = attr[0]
            attr_value = attr[1].strip('"') if len(attr) > 1 else None
            if attr_value:
                match = element.get(attr_name) == attr_value
                return match
            else:
                match = element.has_attr(attr_name)
                return match
    return True

def matches_complex_selector(element, selector):
    while ' + ' in selector:
        selector = selector.replace(' + ', '+')
    while ' > ' in selector:
        selector = selector.replace(' > ', '>')
    parts = selector.split()
    current_element = element
    for i, part in enumerate(reversed(parts)):
        if '>' in part:
            parent_selector, child_selector = part.split('>')
            if not matches_simple_selector(current_element, child_selector.strip()):
                return False
            current_element = current_element.parent
            if current_element is None or not matches_simple_selector(current_element, parent_selector.strip()):
                return False
        elif '+' in part:
            prev_sibling_selector, next_sibling_selector = part.split('+')
            if not matches_simple_selector(current_element, next_sibling_selector.strip()):
                return False
            current_element = current_element.find_previous_sibling()
            if current_element is None or not matches_simple_selector(current_element, prev_sibling_selector.strip()):
                return False
        else:
            if i > 0:
                while current_element is not None and not matches_simple_selector(current_element, part.strip()):
                    current_element = current_element.parent
                if current_element is None:
                    return False
            else:
                if not matches_simple_selector(current_element, part.strip()):
                    return False
    return True



def get_selector_by_html_element(element, css_rules):
    matched_selectors = []
    for selector in css_rules:
        original_selector = selector
        if ',' not in selector:
            if '::' in selector:
                    selector = selector.split('::')[0]
            if ':' in selector:
                selector = selector.split(':')[0]
            if matches_complex_selector(element, selector):
                matched_selectors.append(original_selector)
        else:
            subgroups = selector.split(',')
            for subgroup in subgroups:
                if '::' in subgroup:
                    subgroup = subgroup.split('::')[0]
                if ':' in subgroup:
                    subgroup = subgroup.split(':')[0]
                if matches_complex_selector(element, subgroup):
                    matched_selectors.append(original_selector)

    return matched_selectors


class CSSInteractor:
    def __init__(self, html_file_path):
        self.html_file_path = html_file_path
        # write it to a temp html file
        with open(html_file_path, 'r') as f:
            self.html = f.read()

        self.root_path = os.path.dirname(self.html_file_path)
        self.soup = BeautifulSoup(open(self.html_file_path), 'html.parser')
        
        # get all css files path
        self.css_files = [os.path.join(self.root_path, link['href']) for link in self.soup.find_all('link', rel='stylesheet') if "http" not in link['href']]
        self.css_sheet = {}
        for css_file in self.css_files:
            self.css_sheet[css_file] = cssutils.parseFile(css_file)

        # record this to so we can revert back
        self.last_edit = None


    """
    We only have four acions in total for the agent to take:
    1. select a rule
    This returns the rule and the css file it belongs to. The agent can speculatively select a rule and view its properties.
    2. edit a rule
    This edits a rule. The agent can change the value of a property of a rule.
    3. insert a rule
    This inserts a new rule. The agent can add a new rule with a selector and properties.
    4. revert last edit
    This reverts the last edit. The agent can undo the last edit, if it believes it was a mistake.

    Only after editing a rule or inserting a rule, we will take a screenshot of the page and send it to the agent. So we only write the updated sheet to the css file within these two actions.
    """

    async def finalize(self): # this is not an action but the final step of the task
        if not os.path.exists(os.path.join(self.root_path, "new_screenshot.png")):
            # takes a screenshot anyways
            await take_screenshot(self.html_file_path, os.path.join(self.root_path, "new_screenshot.png"))

    
    def get_selectors_by_html_elements(self, find_all_arguments: str):
        """
        This action takes one argument, the find_all_arguments argument, which should be a specification like "'a', {'data-custom': 'custom-value'}, string='haha'", which should be the valid arguments that can directly pass to the find_all method of BeautifulSoup.
        """
        find_all_arguments = f'self.soup.find_all({find_all_arguments})'
        # print(find_all_arguments)
        elements = eval(find_all_arguments)
        # it's possible that len(elements) == 0, pay attention to this

        matched_selectors = set()
        for element in elements:
            for css_file, sheet in self.css_sheet.items():
                for rule in sheet:
                    if rule.type != rule.STYLE_RULE:
                        continue
                    try:
                        selectors = get_selector_by_html_element(element, [rule.selectorText])
                    except Exception as e:
                        # print(e)
                        # print("exception:", element, rule.selectorText)
                        selectors = []
                        continue
                    matched_selectors.update(selectors)
        return elements, list(matched_selectors)

  
    def select_rule(self, selector):
        """
        This action only takes one argument, the selector of the rule, which should be a string.
        """
        selector = selector.strip().strip('"').strip("'")
        for css_file, sheet in self.css_sheet.items():
            for rule in sheet:
                if rule.type != rule.STYLE_RULE:
                    continue
                if rule.selectorText == selector:
                    return rule, css_file
        return None, None


    async def edit_rule(self, selector, property_name, value):
        """
        This action takes three arguments: the selector of the rule, the property name, and the new value of the property.
        """
        selector = selector.strip().strip('"').strip("'")
        property_name = property_name.strip().strip('"').strip("'")
        value = value.strip().strip('"').strip("'")
        rule, css_file = self.select_rule(selector)
        if css_file is None:
            return False
        sheet = self.css_sheet[css_file]
        if rule:
            if rule.style.getPropertyValue(property_name):
                self.last_edit = {
                    "type": "alter",
                    "css_file": css_file, 
                    "selector": selector, 
                    "property_name": property_name, "old_value": rule.style.getPropertyValue(property_name),
                    "new_value": value
                    }
            else:
                self.last_edit = {
                    "type": "add_property",
                    "css_file": css_file, 
                    "selector": selector, 
                    "property_name": property_name, "new_value": value
                    }
                
            rule.style.setProperty(property_name, value)
            with open(css_file, 'w') as f:
                # write the updated sheet to the css file, decode the css text to utf-8
                f.write(sheet.cssText.decode('utf-8'))

            
            # take a screenshot
            if os.path.exists(os.path.join(self.root_path, "new_screenshot.png")):
                os.remove(os.path.join(self.root_path, "new_screenshot.png"))
            print("ready to take screenshot:", os.path.join(self.root_path, "new_screenshot.png"))
            await take_screenshot(self.html_file_path, os.path.join(self.root_path, "new_screenshot.png"))
            print("screenshot taken")

            return True
        return False


    async def insert_rule(self, rule_json):
        """
        This action takes two arguments: the css file path and the rule to insert.
        The rule should be a dictionary with two keys: 'selector' and 'properties'.
        """
        
        # I finally decided to directly write to the first css file in self.css_files rather than taking a css_file argument.
        css_file = self.css_files[0]

        sheet = self.css_sheet[css_file]
        rule = cssutils.css.CSSStyleRule(selectorText=rule_json['selector'])
        for prop, val in rule_json['properties'].items():
            rule.style.setProperty(prop, val)
        self.last_edit = {
            "type": "insert",
            "css_file": css_file, 
            "selector": rule_json['selector'], 
            "properties": rule_json['properties']
            }
        sheet.insertRule(rule, index=len(sheet.cssRules))

        with open(css_file, 'w') as f:
                # write the updated sheet to the css file, decode the css text to utf-8
                f.write(sheet.cssText.decode('utf-8'))

        # take a screenshot
        if os.path.exists(os.path.join(self.root_path, "new_screenshot.png")):
            os.remove(os.path.join(self.root_path, "new_screenshot.png"))
        await take_screenshot(self.html_file_path, os.path.join(self.root_path, "new_screenshot.png"))

        return True


    def revert_last_edit(self):
        """
        This action takes no arguments.
        """
        if self.last_edit:
            sheet = self.css_sheet[self.last_edit['css_file']]
            if self.last_edit['type'] == "alter":
                rule, _ = self.select_rule(self.last_edit['selector'])
                rule.style.setProperty(self.last_edit['property_name'], self.last_edit['old_value'])
            elif self.last_edit['type'] == "add_property":
                rule, _ = self.select_rule(self.last_edit['selector'])
                rule.style.removeProperty(self.last_edit['property_name'])
            elif self.last_edit['type'] == "insert":
                # check whether the last rule is the one we inserted
                if sheet.cssRules[-1].selectorText == self.last_edit['selector']:
                    sheet.deleteRule(len(sheet.cssRules)-1)
                else:
                    print("The last edit is not the one we inserted!")
            with open(self.last_edit['css_file'], 'w') as f:
                f.write(sheet.cssText.decode('utf-8'))
            return True
        return False

    

