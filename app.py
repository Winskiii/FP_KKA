from flask import Flask, render_template, request, jsonify
import heapq
import networkx as nx
import matplotlib.pyplot as plt

app = Flask(__name__)

# Data city_map and estimated_distances
city_map = {
    'SURABAYA': {'SIDOARJO': 5, 'GRESIK': 9, 'MOJOKERTO': 4},
    'SIDOARJO': {'SURABAYA': 5, 'GRESIK': 3, 'JOMBANG': 7},
    'GRESIK': {'SURABAYA': 9, 'SIDOARJO': 3, 'MOJOKERTO': 2, 'JOMBANG': 6, 'MALANG': 3},
    'MOJOKERTO': {'SURABAYA': 4, 'GRESIK': 2, 'MALANG': 8},
    'JOMBANG': {'SIDOARJO': 7, 'GRESIK': 6, 'MALANG': 5},
    'MALANG': {'GRESIK': 3, 'MOJOKERTO': 8, 'JOMBANG': 5}
}

estimated_distances = {
    'SURABAYA': {'SURABAYA': 0, 'SIDOARJO': 70, 'GRESIK': 95, 'MOJOKERTO': 50, 'JOMBANG': 60, 'MALANG': 90},
    'SIDOARJO': {'SURABAYA': 70, 'SIDOARJO': 0, 'GRESIK': 80, 'MOJOKERTO': 40, 'JOMBANG': 50, 'MALANG': 60},
    'GRESIK': {'SURABAYA': 95, 'SIDOARJO': 80, 'GRESIK': 0, 'MOJOKERTO': 55, 'JOMBANG': 65, 'MALANG': 75},
    'MOJOKERTO': {'SURABAYA': 50, 'SIDOARJO': 40, 'GRESIK': 55, 'MOJOKERTO': 0, 'JOMBANG': 30, 'MALANG': 45},
    'JOMBANG': {'SURABAYA': 60, 'SIDOARJO': 50, 'GRESIK': 65, 'MOJOKERTO': 30, 'JOMBANG': 0, 'MALANG': 35},
    'MALANG': {'SURABAYA': 90, 'SIDOARJO': 60, 'GRESIK': 75, 'MOJOKERTO': 45, 'JOMBANG': 35, 'MALANG': 0}
}

average_duration_per_km = 1
speed_reduction_per_package = 0.1

class Node:
    def __init__(self, location, parent=None, g=0, h=0):
        self.location = location
        self.parent = parent
        self.g = g
        self.h = h
        self.f = g + h

    def __lt__(self, other):
        return self.f < other.f

def heuristic(location, goal, num_packages, w1, w2, w3):
    h1 = estimated_distances[goal][location]
    h2 = average_duration_per_km
    h3 = speed_reduction_per_package * num_packages
    h_cost = (w1 * h1) + (w2 * h2 * h1) + (w3 * h3 * h1)
    print(f"Heuristic for {location} to {goal}: {h_cost}")  # Debugging
    return h_cost

def a_star(start, goal, num_packages, w1, w2, w3):
    open_list = []
    closed_list = set()

    start_node = Node(start, None, 0, heuristic(start, goal, num_packages, w1, w2, w3))
    heapq.heappush(open_list, start_node)

    while open_list:
        current_node = heapq.heappop(open_list)
        closed_list.add(current_node.location)

        if current_node.location == goal:
            path = []
            while current_node:
                path.append(current_node.location)
                current_node = current_node.parent
            return path[::-1]

        for neighbor, distance in city_map[current_node.location].items():
            if neighbor in closed_list:
                continue

            g_cost = current_node.g + distance
            h_cost = heuristic(neighbor, goal, num_packages, w1, w2, w3)
            neighbor_node = Node(neighbor, current_node, g_cost, h_cost)

            if neighbor in (n.location for n in open_list):
                open_node = next(n for n in open_list if n.location == neighbor_node.location)
                if neighbor_node.g < open_node.g:
                    open_list.remove(open_node)
                    heapq.heappush(open_list, neighbor_node)
            else:
                heapq.heappush(open_list, neighbor_node)

    return None

def generate_city_graph():
    G = nx.Graph()

    for city, neighbors in city_map.items():
        for neighbor, distance in neighbors.items():
            G.add_edge(city, neighbor, weight=distance)

    return G

@app.route('/')
def index():
    G = generate_city_graph()

    # Draw the graph
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, font_weight='bold', node_size=700, node_color='skyblue', font_size=8, font_color='black', edge_color='gray')
    plt.savefig('static/city_graph.png')  # Save the graph as a static image
    plt.clf()  # Clear the plot

    return render_template('index.html')

@app.route('/search_route', methods=['POST'])
def search_route():
    start = request.form.get('start').upper()
    goal = request.form.get('goal').upper()

    try:
        num_packages = int(request.form.get('num_packages'))
        w1 = float(request.form.get('w1'))
        w2 = float(request.form.get('w2'))
        w3 = float(request.form.get('w3'))
    except ValueError:
        return jsonify({'result': 'Pastikan jumlah paket dan bobot adalah angka valid.'})

    if w1 + w2 + w3 > 1:
        return jsonify({'result': 'Total bobot (w1 + w2 + w3) tidak boleh lebih dari 1'})

    if w1 + w2 + w3 < 0:
        return jsonify({'result': 'Total bobot (w1 + w2 + w3) tidak boleh kurang dari 1'})

    if start not in city_map or goal not in city_map:
        return jsonify({'result': 'Kota awal atau Kota tujuan invalid.'})

    path = a_star(start, goal, num_packages, w1, w2, w3)
    if path:
        result = "Rute ditemukan: " + " -> ".join(path)
    else:
        result = "Rute tidak ditemukan"

    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True)
