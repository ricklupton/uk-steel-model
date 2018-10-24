import os.path
import json
from glob import glob


margin_left = 150
margin_top = 50


def node_positions_dict(layout):
    return {
        node['id']: {'x': node['geometry']['x'] + margin_left,
                     'y': node['geometry']['y'] + margin_top,
                     'hidden': node['style']['hidden'],
                     'title': node['title']}
        for node in layout['nodes']
    }


def apply_layout(layout, value):
    """Copy layout from `layout` to `value`."""
    node_positions = node_positions_dict(layout)
    for node in value['nodes']:
        if node['id'] in node_positions:
            node.update(node_positions[node['id']])
        else:
            logger.warning('No node position for "%s"', node['id'])
        # if node.get('hidden', False):
        #     node['title'] = ''

    # Copy the page size and scale from the layout Sankey:
    value['pageSize'] = layout['dimensions']
    value['scale'] = layout['metadata']['scale']
    return value


# Load the layout file, and build a map of node positions:
with open(os.path.join(os.path.dirname(__file__), 'sankey_layout.json'), 'r') as f:
    layout = json.load(f)

# Load the Sankey data and apply layout
def process_year(filename, outdir):
    with open(filename, 'r') as f:
        data = json.load(f)

    data = apply_layout(layout, data)
    data['metadata']['title'] = os.path.basename(filename)[len('sankey_'):][:4]

    with open(os.path.join(outdir, os.path.basename(filename)), 'wt') as f:
        json.dump(data, f)


for filename in glob('figures/generated/sankey_*.json'):
    print('Processing', filename)
    process_year(filename, 'figures/with_layout')
