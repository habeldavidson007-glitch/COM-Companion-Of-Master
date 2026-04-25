"""
Web Stack Expert Module for COM
Specialized in HTML, CSS, JavaScript, TypeScript, and modern web frameworks.
"""

import re
from typing import Dict, List, Any, Optional
from tools.base import BaseTool

class WebStackTool(BaseTool):
    """Tool for web development assistance."""
    
    def __init__(self):
        super().__init__()
        self.name = "WebStackTool"
        self.description = "Expert in web development: HTML5, CSS3, JavaScript (ES6+), TypeScript, React, Vue, Angular, Node.js, and modern build tools."
        self.frameworks = ["React", "Vue", "Angular", "Svelte", "Next.js", "Nuxt"]
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Execute web development tasks.
        
        Actions:
        - 'analyze_html': Analyze HTML for semantics and accessibility
        - 'analyze_css': Analyze CSS for best practices
        - 'analyze_js': Analyze JavaScript/TypeScript code
        - 'suggest_component': Suggest component structure
        - 'explain_concept': Explain web development concepts
        - 'generate_template': Generate code templates
        """
        if action == "analyze_html":
            return self.analyze_html(kwargs.get("code", ""))
        elif action == "analyze_css":
            return self.analyze_css(kwargs.get("code", ""))
        elif action == "analyze_js":
            return self.analyze_js(kwargs.get("code", ""), kwargs.get("is_typescript", False))
        elif action == "suggest_component":
            return self.suggest_component(kwargs.get("framework", "react"), kwargs.get("component_type", ""))
        elif action == "explain_concept":
            return self.explain_concept(kwargs.get("concept", ""))
        elif action == "generate_template":
            return self.generate_template(kwargs.get("template_type", "html"))
        else:
            return {"error": f"Unknown action: {action}", "available_actions": [
                "analyze_html", "analyze_css", "analyze_js",
                "suggest_component", "explain_concept", "generate_template"
            ]}
    
    def analyze_html(self, code: str) -> Dict[str, Any]:
        """Analyze HTML for semantics, accessibility, and best practices."""
        issues = []
        suggestions = []
        strengths = []
        
        # Check for DOCTYPE
        if not code.strip().startswith('<!DOCTYPE'):
            issues.append("Missing <!DOCTYPE html> declaration")
        else:
            strengths.append("Has proper DOCTYPE declaration")
        
        # Check for lang attribute
        if '<html' in code and 'lang=' not in code:
            issues.append("Missing 'lang' attribute on <html> element")
        
        # Check for meta viewport
        if '<meta' in code and 'viewport' not in code:
            suggestions.append("Add <meta name='viewport' content='width=device-width, initial-scale=1'> for responsive design")
        
        # Check for semantic elements
        semantic_elements = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']
        found_semantic = [elem for elem in semantic_elements if f'<{elem}' in code]
        
        if not found_semantic and '<div' in code:
            suggestions.append("Use semantic HTML elements (header, nav, main, section, article, footer) instead of generic divs")
        else:
            strengths.append(f"Uses semantic elements: {', '.join(found_semantic)}")
        
        # Check for alt attributes on images
        img_tags = re.findall(r'<img[^>]*>', code)
        imgs_without_alt = [img for img in img_tags if 'alt=' not in img]
        if imgs_without_alt:
            issues.append(f"{len(imgs_without_alt)} image(s) missing 'alt' attribute (accessibility)")
        
        # Check for form labels
        if '<input' in code or '<select' in code or '<textarea' in code:
            if '<label' not in code and 'aria-label' not in code:
                issues.append("Form inputs should have associated <label> elements or aria-label for accessibility")
        
        # Check for button type
        button_tags = re.findall(r'<button[^>]*>', code)
        buttons_without_type = [btn for btn in button_tags if 'type=' not in btn]
        if buttons_without_type:
            suggestions.append("Explicitly set 'type' attribute on <button> elements (button|submit|reset)")
        
        # Check for inline styles
        if 'style=' in code:
            suggestions.append("Avoid inline styles; use external CSS or CSS-in-JS for maintainability")
        
        # Check for deprecated tags
        deprecated = ['font', 'center', 'strike', 'marquee', 'blink']
        found_deprecated = [tag for tag in deprecated if f'<{tag}' in code]
        if found_deprecated:
            issues.append(f"Deprecated tags detected: {', '.join(found_deprecated)}")
        
        return {
            "status": "analyzed",
            "issues": issues,
            "suggestions": suggestions,
            "strengths": strengths,
            "accessibility_score": "good" if len(issues) == 0 else "needs improvement",
            "semantic_score": "good" if found_semantic else "needs improvement"
        }
    
    def analyze_css(self, code: str) -> Dict[str, Any]:
        """Analyze CSS for best practices and performance."""
        issues = []
        suggestions = []
        strengths = []
        
        # Check for !important usage
        important_count = code.count('!important')
        if important_count > 0:
            issues.append(f"Avoid !important ({important_count} occurrences). Refactor specificity instead")
        
        # Check for ID selectors (high specificity)
        if re.search(r'#\w+\s*{', code):
            suggestions.append("Minimize ID selectors; prefer classes for lower specificity and reusability")
        
        # Check for universal selector performance
        if '* {' in code or '*{' in code:
            suggestions.append("Universal selector (*) can impact performance; use more specific selectors")
        
        # Check for vendor prefixes
        vendor_prefixes = ['-webkit-', '-moz-', '-ms-', '-o-']
        has_prefixes = any(prefix in code for prefix in vendor_prefixes)
        if has_prefixes:
            suggestions.append("Consider using Autoprefixer to manage vendor prefixes automatically")
        else:
            strengths.append("No manual vendor prefixes (likely using Autoprefixer or modern properties)")
        
        # Check for CSS variables
        if '--' in code and 'var(' in code:
            strengths.append("Uses CSS custom properties (variables) for maintainability")
        elif code.count(':') > 10 and '--' not in code:
            suggestions.append("Consider CSS custom properties for repeated values (colors, spacing)")
        
        # Check for shorthand properties
        longhand_patterns = [
            (r'margin-top.*margin-right.*margin-bottom.*margin-left', 'margin'),
            (r'padding-top.*padding-right.*padding-bottom.*padding-left', 'padding'),
            (r'border-width.*border-style.*border-color', 'border')
        ]
        for pattern, shorthand in longhand_patterns:
            if re.search(pattern, code, re.DOTALL):
                suggestions.append(f"Use shorthand '{shorthand}' property where applicable")
        
        # Check for flexbox/grid usage
        if 'display: flex' in code or 'display:flex' in code:
            strengths.append("Uses Flexbox for layout")
        if 'display: grid' in code or 'display:grid' in code:
            strengths.append("Uses CSS Grid for layout")
        
        # Check for media queries (responsive design)
        if '@media' in code:
            strengths.append("Implements responsive design with media queries")
        else:
            suggestions.append("Add media queries for responsive design")
        
        return {
            "status": "analyzed",
            "issues": issues,
            "suggestions": suggestions,
            "strengths": strengths,
            "maintainability": "good" if len(issues) == 0 else "needs refactoring"
        }
    
    def analyze_js(self, code: str, is_typescript: bool = False) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code for best practices."""
        issues = []
        suggestions = []
        strengths = []
        
        # Check for var vs let/const
        if re.search(r'\bvar\b', code):
            suggestions.append("Replace 'var' with 'let' or 'const' (block scoping)")
        else:
            strengths.append("Uses 'let'/'const' instead of 'var'")
        
        # Check for arrow functions
        if re.search(r'function\s*\(', code) and '=>' not in code:
            suggestions.append("Consider arrow functions for lexical 'this' binding")
        
        # Check for template literals
        if "+ '" in code or '+ "' in code or "' + " in code or '" + ' in code:
            suggestions.append("Use template literals (`...`) instead of string concatenation")
        else:
            strengths.append("Uses template literals")
        
        # Check for async/await vs .then()
        if '.then(' in code and 'async' not in code:
            suggestions.append("Consider async/await for cleaner asynchronous code")
        elif 'async' in code and 'await' in code:
            strengths.append("Uses async/await pattern")
        
        # Check for console statements
        console_matches = re.findall(r'console\.(log|warn|error|debug)\s*\(', code)
        if console_matches:
            suggestions.append(f"Remove console statements ({len(console_matches)} found) for production")
        
        # Check for strict equality
        if re.search(r'==[^=]|[^=!]=[^=]', code):
            issues.append("Use strict equality (=== and !==) instead of loose equality (== and !=)")
        else:
            strengths.append("Uses strict equality operators")
        
        # Check for destructuring
        if re.search(r'\w+\.\w+', code) and '=' not in code.split('.')[0]:
            if 'const {' not in code and 'let {' not in code:
                suggestions.append("Use destructuring assignment for cleaner object/array access")
        
        # TypeScript-specific checks
        if is_typescript:
            if ': any' in code:
                suggestions.append("Avoid 'any' type; use specific types or interfaces")
            if 'interface' not in code and 'type ' not in code:
                suggestions.append("Define interfaces or types for better type safety")
            else:
                strengths.append("Uses TypeScript interfaces/types")
        
        # Check for modules
        if 'require(' in code:
            suggestions.append("Consider ES6 modules (import/export) instead of CommonJS require()")
        elif 'import ' in code and 'export' in code:
            strengths.append("Uses ES6 module system")
        
        return {
            "status": "analyzed",
            "issues": issues,
            "suggestions": suggestions,
            "strengths": strengths,
            "modern_es6_usage": "good" if len(suggestions) == 0 else "can be modernized"
        }
    
    def suggest_component(self, framework: str, component_type: str) -> Dict[str, Any]:
        """Suggest component structure for various frameworks."""
        framework = framework.lower()
        
        structures = {
            "react": f'''
// {component_type or 'Component'}.jsx
import React, {{ useState, useEffect }} from 'react';
import PropTypes from 'prop-types';

const {component_type or 'MyComponent'} = ({{ title, items, onAction }}) => {{
  const [state, setState] = useState(null);
  
  useEffect(() => {{
    // Component did mount / update logic
    return () => {{
      // Cleanup (component will unmount)
    }};
  }}, [/* dependencies */]);
  
  const handleClick = () => {{
    onAction?.();
  }};
  
  return (
    <div className="{(component_type or 'my').toLowerCase()}-component">
      {{title && <h2>{{title}}</h2>}}
      {{items?.map((item, idx) => (
        <div key={{idx}}>{{item}}</div>
      ))}}
      <button onClick={{handleClick}}>Action</button>
    </div>
  );
}};

{component_type or 'MyComponent'}.propTypes = {{
  title: PropTypes.string,
  items: PropTypes.arrayOf(PropTypes.string),
  onAction: PropTypes.func
}};

export default {component_type or 'MyComponent'};
''',
            "vue": f'''
<!-- {component_type or 'Component'}.vue -->
<template>
  <div class="{(component_type or 'my').toLowerCase()}-component">
    <h2 v-if="title">{{{{ title }}}}</h2>
    <div v-for="(item, idx) in items" :key="idx">
      {{{{ item }}}}
    </div>
    <button @click="handleAction">Action</button>
  </div>
</template>

<script>
export default {{
  name: '{component_type or 'MyComponent'}',
  props: {{
    title: {{ type: String, default: '' }},
    items: {{ type: Array, default: () => [] }}
  }},
  emits: ['action'],
  setup(props, {{ emit }}) {{
    const handleAction = () => {{
      emit('action');
    }};
    
    return {{ handleAction }};
  }}
}};
</script>

<style scoped>
.{(component_type or 'my').toLowerCase()}-component {{
  /* Styles here */
}}
</style>
''',
            "angular": f'''
// {component_type or 'component'}.component.ts
import {{ Component, Input, Output, EventEmitter }} from '@angular/core';

@Component({{
  selector: 'app-{(component_type or 'my').lower()}',
  templateUrl: './{(component_type or 'my').lower()}.component.html',
  styleUrls: ['./{(component_type or 'my').lower()}.component.css']
}})
export class {component_type or 'My'}Component {{
  @Input() title: string = '';
  @Input() items: string[] = [];
  @Output() action = new EventEmitter<void>();
  
  handleAction(): void {{
    this.action.emit();
  }}
}}
''',
            "svelte": f'''
<!-- {component_type or 'Component'}.svelte -->
<script>
  export let title = '';
  export let items = [];
  
  function handleAction() {{
    // Dispatch event or call parent function
  }}
</script>

<div class="{(component_type or 'my').toLowerCase()}-component">
  {{#if title}}
    <h2>{{title}}</h2>
  {{/if}}
  
  {{#each items as item, i}}
    <div key={{i}}>{{item}}</div>
  {{/each}}
  
  <button on:click={{handleAction}}>Action</button>
</div>

<style>
  .{(component_type or 'my').toLowerCase()}-component {{
    /* Styles */
  }}
</style>
'''
        }
        
        return {
            "framework": framework,
            "component_type": component_type or "Generic",
            "structure": structures.get(framework, f"Framework '{framework}' not supported. Try: react, vue, angular, svelte"),
            "best_practices": [
                "Keep components small and focused on single responsibility",
                "Use props for data flow, events for communication up",
                "Implement proper error boundaries/loading states",
                "Write unit tests for component logic"
            ]
        }
    
    def explain_concept(self, concept: str) -> str:
        """Explain web development concepts."""
        concept_lower = concept.lower()
        
        explanations = {
            "virtual_dom": """
Virtual DOM (React):
A lightweight copy of the real DOM used for efficient updates.

How it works:
1. Component state changes
2. New Virtual DOM tree created
3. Diffing algorithm compares old vs new
4. Minimal updates applied to real DOM

Benefits:
- Performance optimization
- Declarative programming model
- Cross-platform compatibility (React Native)

Example:
function Counter() {
  const [count, setCount] = useState(0);
  // Virtual DOM tracks count changes
  // Only updates the text node, not entire component
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
""",
            "reactive": """
Reactivity (Vue/Svelte):
Automatic UI updates when data changes.

Vue 3 Reactivity:
- Uses Proxy-based reactivity system
- Tracks dependencies automatically
- Batched updates for performance

Example (Vue):
<script setup>
import { ref } from 'vue';

const count = ref(0);
// Template automatically updates when count.value changes
</script>

<template>
  <button @click="count++">{{ count }}</button>
</template>

Svelte:
- Compile-time reactivity
- No virtual DOM overhead
- True reactive statements with $:

$: doubled = count * 2;
""",
            "closure": """
Closures in JavaScript:
A function that remembers its lexical scope even when executed outside it.

Example:
function createCounter() {
  let count = 0;  // Private variable
  
  return {
    increment: () => count++,
    decrement: () => count--,
    getCount: () => count
  };
}

const counter = createCounter();
counter.increment();
counter.getCount();  // 1
// 'count' is inaccessible directly (encapsulation)

Use Cases:
- Data privacy/emulation of private methods
- Function factories
- Event handlers with preserved state
- Currying and partial application
""",
            "promise": """
Promises in JavaScript:
Object representing eventual completion (or failure) of async operation.

States: Pending → Fulfilled or Rejected

Basic Usage:
fetch('/api/data')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));

Async/Await (syntactic sugar):
async function fetchData() {
  try {
    const response = await fetch('/api/data');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(error);
  }
}

Promise.all (parallel execution):
const [users, posts] = await Promise.all([
  fetch('/users'),
  fetch('/posts')
]);
""",
            "css_specificity": """
CSS Specificity:
Determines which style rule applies when multiple rules match.

Specificity Hierarchy (highest to lowest):
1. !important (avoid when possible)
2. Inline styles (1000)
3. ID selectors (#id) (100)
4. Class selectors (.class), attributes, pseudo-classes (10)
5. Element selectors (div, p), pseudo-elements (1)

Calculation:
#nav .item:hover  = 100 + 10 + 10 = 120
.header .nav .item = 10 + 10 + 10 = 30
div ul li          = 1 + 1 + 1 = 3

Best Practices:
- Avoid IDs for styling
- Use BEM or similar naming conventions
- Keep specificity low and consistent
- Use CSS custom properties for theming
""",
            "event_bubbling": """
Event Bubbling & Capturing:
Event propagation mechanisms in the DOM.

Bubbling (default):
Event starts at target and bubbles up to document
child → parent → grandparent → ... → document

Capturing:
Event goes from document down to target
document → ... → grandparent → parent → child

Example:
<div id="parent">
  <button id="child">Click</button>
</div>

// Bubbling (default)
child.addEventListener('click', (e) => {
  console.log('Child clicked');
});

parent.addEventListener('click', (e) => {
  console.log('Parent clicked (bubbled)');
});

// Capturing
parent.addEventListener('click', (e) => {
  console.log('Parent captured');
}, true);  // Third parameter: useCapture

Stop Propagation:
e.stopPropagation();  // Prevent bubbling/capturing
e.preventDefault();   // Prevent default behavior
"""
        }
        
        for key, explanation in explanations.items():
            if key.replace('_', ' ') in concept_lower or key in concept_lower:
                return explanation
        
        return f"Concept '{concept}' not found. Try: virtual_dom, reactive, closure, promise, css_specificity, event_bubbling"
    
    def generate_template(self, template_type: str) -> str:
        """Generate web development templates."""
        templates = {
            "html": '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Page description">
  <title>Page Title</title>
  <link rel="stylesheet" href="styles.css">
  <link rel="icon" href="favicon.ico" type="image/x-icon">
</head>
<body>
  <header>
    <nav>
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </nav>
  </header>
  
  <main>
    <h1>Main Heading</h1>
    <section>
      <h2>Section Title</h2>
      <p>Content goes here...</p>
    </section>
  </main>
  
  <footer>
    <p>&copy; 2024 Company Name</p>
  </footer>
  
  <script src="script.js" defer></script>
</body>
</html>
''',
            "package_json": '''{
  "name": "my-web-project",
  "version": "1.0.0",
  "description": "Project description",
  "main": "src/index.js",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src/",
    "test": "vitest",
    "format": "prettier --write src/"
  },
  "keywords": [],
  "author": "",
  "license": "MIT",
  "devDependencies": {
    "eslint": "^9.0.0",
    "prettier": "^3.0.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0"
  },
  "dependencies": {}
}
''',
            "gitignore_web": '''# Dependencies
node_modules/
.pnp
.pnp.js

# Build output
dist/
build/

# Environment files
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log
npm-debug.log*

# Testing
coverage/

# Misc
.cache/
.temp/
'''
        }
        
        return templates.get(template_type, f"Template '{template_type}' not found. Available: html, package_json, gitignore_web")
