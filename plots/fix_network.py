import re
import json

# Read the network.html file
with open('network.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the Plotly.newPlot call
match = re.search(r'Plotly\.newPlot\(\s*"[^"]+",\s*(\[.*?\]),\s*(\{.*?\}),\s*(\{[^}]*\})\s*\)', content, re.DOTALL)
if not match:
    print("Could not find Plotly.newPlot call")
    exit(1)

data_str = match.group(1)
layout_str = match.group(2)
config_str = match.group(3)

# Parse the data and layout as JSON
data = json.loads(data_str)
layout = json.loads(layout_str)

print(f"Found {len(data)} traces")

# The last trace (index 52) is the combined node trace
node_trace = data[-1]
print(f"Node trace has {len(node_trace['x'])} nodes")

# Extract node data
node_names = node_trace['text']
node_x = node_trace['x']
node_y = node_trace['y']
node_hovertext = node_trace['hovertext']
node_colors = node_trace['marker']['color']

# Remove the combined node trace
data = data[:-1]

# Create individual node traces
for i in range(len(node_names)):
    new_trace = {
        "hoverinfo": "text",
        "hovertext": [node_hovertext[i]],
        "marker": {
            "color": [node_colors[i]],
            "colorbar": node_trace['marker']['colorbar'] if i == 0 else None,
            "colorscale": node_trace['marker']['colorscale'],
            "line": {"color": "black", "width": 2},
            "opacity": 0.75,
            "size": 40,
            "cmin": min(node_colors),
            "cmax": max(node_colors)
        },
        "mode": "markers+text",
        "name": node_names[i],
        "showlegend": False,
        "text": [node_names[i]],
        "textfont": {"color": "#ffffff", "size": 10},
        "textposition": "top center",
        "x": [node_x[i]],
        "y": [node_y[i]],
        "type": "scatter"
    }
    # Remove colorbar from all but the first node trace
    if i != 0:
        del new_trace['marker']['colorbar']
    data.append(new_trace)

print(f"Now have {len(data)} traces")

# Update the dropdown buttons to control node visibility
# Traces 0-48: edges (49 traces)
# Traces 49-51: legend entries (3 traces)
# Traces 52-72: individual nodes (21 traces)

num_edges = 49
num_legend = 3
num_nodes = 21
total_traces = num_edges + num_legend + num_nodes  # 73

# Create new buttons
new_buttons = []

# "All" button - show everything
all_visible = [True] * total_traces
new_buttons.append({
    "args": [{"visible": all_visible}],
    "label": "All",
    "method": "update"
})

# Individual node buttons - show only that node, hide others
for i, name in enumerate(node_names):
    visible = [True] * num_edges  # Show all edges
    visible += [True] * num_legend  # Show legend
    # For nodes, only show the selected one
    for j in range(num_nodes):
        visible.append(i == j)
    
    new_buttons.append({
        "args": [{"visible": visible}],
        "label": name,
        "method": "update"
    })

# Update the layout with new buttons
layout['updatemenus'][0]['buttons'] = new_buttons

# Update annotation text
for ann in layout.get('annotations', []):
    if ann.get('text') == 'Show Edges for:':
        ann['text'] = 'Show Node:'

# Reconstruct the HTML
new_data_str = json.dumps(data, separators=(',', ':'))
new_layout_str = json.dumps(layout, separators=(',', ':'))

# Get the div ID
div_id_match = re.search(r'Plotly\.newPlot\(\s*"([^"]+)"', content)
div_id = div_id_match.group(1)

# Replace in content
new_plotly_call = f'Plotly.newPlot("{div_id}",{new_data_str},{new_layout_str},{config_str})'

# Find and replace the entire Plotly.newPlot call
# Use string find/replace instead of regex to avoid escape issues
start_marker = 'Plotly.newPlot('
start_idx = content.find(start_marker)
# Find the closing of the Plotly.newPlot call - need to match parentheses
paren_count = 0
end_idx = start_idx
in_string = False
escape_next = False
for i, char in enumerate(content[start_idx:], start_idx):
    if escape_next:
        escape_next = False
        continue
    if char == '\\':
        escape_next = True
        continue
    if char == '"' and not escape_next:
        in_string = not in_string
    if not in_string:
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
            if paren_count == 0:
                end_idx = i + 1
                break

old_call = content[start_idx:end_idx]
new_content = content[:start_idx] + new_plotly_call + content[end_idx:]

# Write the new file
with open('network.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done! network.html has been updated.")
print(f"Dropdown now controls visibility of {num_nodes} individual node traces")
