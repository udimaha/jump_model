import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

DATA_PATH = Path("~/university/jump_model_exp/256_island_out").expanduser()
assert DATA_PATH.exists() and DATA_PATH.is_dir()

distribution = {}

for data_f in DATA_PATH.glob("*.json"):
	with data_f.open("r") as f:
		data = json.load(f)
	edge_len = data['expected_edge_len']
	stats = data['island_stats']
	for k, v in stats.items():
		assert len(v) == 1
		distribution.setdefault(k, {}).setdefault(edge_len, []).append(v[0])

# # Make a separate list for each airline
# x1 = list(flights[flights['name'] == 'United Air Lines Inc.']['arr_delay'])
# x2 = list(flights[flights['name'] == 'JetBlue Airways']['arr_delay'])
# x3 = list(flights[flights['name'] == 'ExpressJet Airlines Inc.']['arr_delay'])
# x4 = list(flights[flights['name'] == 'Delta Air Lines Inc.']['arr_delay'])
# x5 = list(flights[flights['name'] == 'American Airlines Inc.']['arr_delay'])
#
# # Assign colors for each airline and the names
# colors = ['#E69F00', '#56B4E9', '#F0E442', '#009E73', '#D55E00']
# names = ['United Air Lines Inc.', 'JetBlue Airways', 'ExpressJet Airlines Inc.'',
# 													 'Delta Air Lines Inc.', 'American Airlines Inc.']

# Make the histogram using a list of lists
# Normalize the flights and assign colors and names
size_5 = sorted({k: v for k, v in distribution['5'].items() if float(k) % 0.2 == 0}.items())
plt.hist([v for _, v in size_5], bins=len(size_5),
		 label=[f"EdgeLen: {v}" for v, _ in size_5])

# Plot formatting
plt.legend()
plt.xlabel('Occurrences')
plt.ylabel('Edge Length')
plt.title('Occurences of size 5 islands')
plt.show()
