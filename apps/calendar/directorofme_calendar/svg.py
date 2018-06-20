import cairosvg

SVG_START = """
<svg xmlns="http://www.w3.org/2000/svg" height="500" width="1008" viewBox="0 0 500 1008">
"""

SVG_CALENDAR = """
  <!-- calendar -->
  <g>
      <polygon points="4,104 54,4 954,4 1004,104, 954,204, 54,204" style="fill:none;stroke:#092421;stroke-width:4" />
      <path d="M 54 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
      <text x="64" y="200" color="#092421" font-family="Arial" font-size="40" font-weight="bold">9a</text>

      <path d="M 154 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
      <text x="160" y="200" color="#092421" font-family="Arial" font-size="40" font-weight="bold">10a</text>
<path d="M 254 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
      <text x="260" y="200" color="#092421" font-family="Arial" font-size="40" font-weight="bold">11a</text>

      <path d="M 354 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
      <text x="365" y="200" color="#092421" font-family="Arial" font-size="40" font-weight="bold">12p</text>

      <path d="M 454 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
      <text x="460" y="200" color="#092421" font-family="Arial" font-size="40" font-weight="bold">1p</text>

      <path d="M 554 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
      <text x="560" y="200" color="#092421" font-family="Arial" font-size="40" font-weight="bold">2p</text>

      <path d="M 654 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
      <text x="660" y="200" color="#092421" font-family="Arial" font-size="40" font-weight="bold">3p</text>

      <path d="M 754 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
      <text x="760" y="200" color="#092421" font-family="Arial" font-size="40" font-weight="bold">4p</text>

      <path d="M 854 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
      <text x="860" y="200" color="#092421" font-family="Arial" font-size="40" font-weight="bold">5p</text>

      <path d="M 954 4 V 204" fill="none" stroke="#092421" stroke-width="4" stroke-dasharray="5,5" />
  </g>
"""

SVG_LEGEND = """ <!-- legend -->
  <g opacity=".66">
    <rect x="60" y="250" height="30" width="30" fill="#092421" />
    <text x="96" y="275" font-family="Arial" font-size="30" font-weight="bold" color="#092421">Small Tasks</text>

    <rect x="280" y="250" height="30" width="30" fill="#FF0000" />
    <text x="316" y="275" font-family="Arial" font-size="30" font-weight="bold" color="#092421">Meeting</text>

    <rect x="440" y="250" height="30" width="30" fill="#CCCCCC" />
    <text x="476" y="275" font-family="Arial" font-size="30" font-weight="bold" color="#092421">Meeting Prep/Recovery</text>

    <rect x="820" y="250" height="30" width="30" fill="#1AA79D" />
    <text x="856" y="275" font-family="Arial" font-size="30" font-weight="bold" color="#092421">Flow</text>
  </g>
"""

SVG_END = "</svg>"


class BlockType():
        flow = 'Flow'
        meeting = 'Meeting'
        meeting_prep_or_recovery = 'Meeting Prep/Recovery'
        small_task = 'Small Tasks'

COLORS = {
	BlockType.flow: '#1AA79D',
	BlockType.meeting: '#FF0000',
	BlockType.meeting_prep_or_recovery: '#CCCCCC',
	BlockType.small_task: '#092421',
}

def __string_to_float(string_time):
	return int(string_time.split(":")[0]) + int(string_time.split(":")[1])/60.0

def svg_from_blocks(start_of_day, end_of_day, blocks):
	'''
	start_of day: time of the form `HH:MM` in 24 hour time
	end_of_day: time of the form `HH:MM` in 24 hour time
	blocks:  an ordered list of dictionaries:
	 { "type": BlockType, "start": "HH:MM", "end": "HH:MM" }

	returns: string containing svg data
	'''
	svg_blocks = '<g opacity=".66">\n'
	
	day_start_float = __string_to_float(start_of_day)
	day_end_float = __string_to_float(end_of_day)
	
	# Get the denominator for the "size of the block"
	denom = day_end_float - day_start_float

	for index, block in enumerate(blocks):
		block_start = __string_to_float(block['start']) 
		block_end = __string_to_float(block['end'])
		block_width = (block_end - block_start) * 1000 / denom
		block_color = COLORS[block['type']]
		start_pos = (block_start - day_start_float) * 1000 / denom

		# The first one
		if index == 0:
			# if the block doesnt start at the beginning of the day, we need to draw an empty triangle before it
			if block_start > day_start_float:
				poly = '<polygon points="4,104 54,4 {width},4 {width},204, 54,204" fill="#FFFFFF" />\n'.format(
					**{'width': block_start})
				rect = '<rect x="{}" y="4" height="200" width="{}" fill="{}" />\n'.format(
					start_pos, block_width, COLORS[block['type']])
				svg_blocks = '{}{}{}'.format(svg_blocks, poly, rect)
			else:
				poly = '<polygon points="4,104 54,4 {width},4 {width},204, 54,204" fill="{block_color}" />\n'.format(
					**{'width': block_width, 'block_color': block_color})
				svg_blocks = '{}{}'.format(svg_blocks, poly)
				start_pos = block_width + 4

		elif index == len(blocks) - 1:
			# if the last one doesnt end at the end of the day, we need to draw an empty triangle at the end
			if block_end >= day_end_float:
				poly = '<polygon points="{start_pos},4 954,4 1004,104 954,204, {start_pos},204" fill="{block_color}" />\n'.format(
					**{'width': block_width, 'block_color': block_color, 'start_pos': start_pos})
			else:
				rect = '<rect x="{}" y="4" height="200" width="{}" fill="{}" />\n'.format(
					start_pos, block_width, COLORS[block['type']])
				poly = '{rect}<polygon points="{block_width},4 954,4 1004,104 954,204, {block_width},204" fill="#FFFFFF" />\n'.format(
				 	**{'rect': rect, 'block_width': block_width})	
      			svg_blocks = '{}{}'.format(svg_blocks, poly)
		else:
			rect = '<rect x="{}" y="4" height="200" width="{}" fill="{}" />\n'.format(
				start_pos, block_width, COLORS[block['type']])
      			svg_blocks = '{}{}'.format(svg_blocks, rect)

			start_pos = block_width + 4
		
	svg_blocks = '{}</g>\n'.format(svg_blocks)

    	return '{}{}{}{}{}'.format(SVG_START, svg_blocks, SVG_CALENDAR, SVG_LEGEND, SVG_END)

def svg_to_png(svg_string):
	''' Returns bytes for a PNG. takes an svg string as an arg. '''
	return cairosvg.svg2png(bytestring=str.encode(svg_string)


#svg = svg_from_blocks("9:00", "17:00", 
#		[{'type': 'Meeting', 'start': '9:00', 'end': '10:30'}, 
#		 {'type': 'Meeting', 'start': '11:00', 'end': '11:45'}, 
#		 {'type': "Meeting Prep/Recovery", 'start': '11:45', 'end': '12:00'}, 
#		 {'type': 'Flow', 'start': '12:00', 'end': '17:00'}])
#
#print(svg)
