import 'package:flutter/material.dart';
import 'package:http/http.dart' as http; // Per effettuare richieste HTTP
import 'dart:convert';

// ignore: unused_import
import 'package:intl/date_time_patterns.dart';

void main() => runApp(const InjuryManagerApp());

// Data Models
class Injury {
  final String category;
  final String type;
  final List<String> exercises;
  final DateTime date;

  const Injury({
    required this.category,
    required this.type,
    required this.exercises,
    required this.date,
  });
}

class Player {
  final String name;
  final List<Injury> injuries;

  Player({required this.name, required this.injuries});
}

class InjuryManagerApp extends StatelessWidget {
  const InjuryManagerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BasketMed Tracker',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2E7D32),
          secondary: const Color(0xFFFFA000),
        ),
        fontFamily: 'Inter',
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
      ),
      home: const PlayersScreen(),
    );
  }
}

class PlayersScreen extends StatefulWidget {
  const PlayersScreen({super.key});

  @override
  State<PlayersScreen> createState() => _PlayersScreenState();
}

class _PlayersScreenState extends State<PlayersScreen> {
  final List<Player> players = [
    Player(name: "enea", injuries: []),
    Player(name: "jacopo", injuries: []),
  ];

  void _addNewPlayer(String name) {
    setState(() => players.add(Player(name: name, injuries: [])));
  }

  void _addInjury(int playerIndex, Injury injury) {
    setState(() => players[playerIndex].injuries.add(injury));
  }

  void _removeInjury(int playerIndex, int injuryIndex) {
    setState(() => players[playerIndex].injuries.removeAt(injuryIndex));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Players'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add),
            onPressed: () => _showAddDialog(context),
          ),
        ],
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: players.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder:
            (ctx, index) => _PlayerCard(
              player: players[index],
              onAdd: () => _showInjurySheet(context, index),
              onRemove: (injuryIndex) => _removeInjury(index, injuryIndex),
            ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.person_add),
        label: const Text('Add Player'),
        onPressed: () => _showAddDialog(context),
      ),
    );
  }

  void _showAddDialog(BuildContext context) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('New Player'),
            content: TextField(
              controller: controller,
              decoration: const InputDecoration(
                labelText: 'Player Name',
                border: OutlineInputBorder(),
              ),
            ),
            actions: [
              TextButton(
                onPressed: Navigator.of(ctx).pop,
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: () {
                  if (controller.text.trim().isNotEmpty) {
                    _addNewPlayer(controller.text.trim());
                    Navigator.pop(ctx);
                  }
                },
                child: const Text('Save'),
              ),
            ],
          ),
    );
  }

  void _showInjurySheet(BuildContext context, int playerIndex) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder:
          (ctx) => _InjurySelector(
            onSelect: (injury) => _addInjury(playerIndex, injury),
          ),
    );
  }
}

class _PlayerCard extends StatelessWidget {
  final Player player;
  final VoidCallback onAdd;
  final Function(int) onRemove;

  const _PlayerCard({
    required this.player,
    required this.onAdd,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Dismissible(
      key: ValueKey(player.name),
      direction: DismissDirection.endToStart,
      background: Container(
        color: Colors.red,
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        child: const Icon(Icons.delete, color: Colors.white),
      ),
      confirmDismiss: (_) async {
        return await showDialog(
          context: context,
          builder:
              (ctx) => AlertDialog(
                title: const Text('Delete Player?'),
                content: const Text('This action cannot be undone'),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(ctx, false),
                    child: const Text('Cancel'),
                  ),
                  FilledButton(
                    onPressed: () => Navigator.pop(ctx, true),
                    child: const Text('Delete'),
                  ),
                ],
              ),
        );
      },
      child: Card(
        child: ListTile(
          leading: const Icon(Icons.person_pin, size: 40),
          title: Text(player.name),
          subtitle: Text(
            '${player.injuries.length} active injuries',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          trailing: IconButton(
            icon: const Icon(Icons.add_chart),
            onPressed: onAdd,
          ),
          onTap:
              () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder:
                      (_) => _InjuryDetails(
                        injuries: player.injuries,
                        onRemove: onRemove,
                      ),
                ),
              ),
        ),
      ),
    );
  }
}

class _InjurySelector extends StatelessWidget {
  final Function(Injury) onSelect;

  const _InjurySelector({required this.onSelect});

  final List<Map<String, dynamic>> _categories = const [
    {
      'category': 'Ankle',
      'icon': Icons.airline_seat_legroom_reduced,
      'types': [
        {
          'name': 'Lateral Ankle Sprain',
          'exercises': [
            'Ankle circles (3×10 directions)',
            'Single-leg balance (3×30″)',
          ],
        },
        {
          'name': 'Achilles Tendinopathy',
          'exercises': [
            'Eccentric calf raises (3×15)',
            'Calf stretching (3×30″)',
            'Plantar mobilization (3×15)',
          ],
        },
      ],
    },
    {
      'category': 'Knee',
      'icon': Icons.hiking,
      'types': [
        {
          'name': 'ACL & MCL sprains / ACL tear',
          'exercises': ['Quadriceps isometrics (3x10)', 'Mini-squats (3x12)'],
        },
        {
          'name': 'Patellar Tendinopathy',
          'exercises': ['Static Lunges (3x10)'],
        },
        {
          'name': 'Meniscus Tear',
          'exercises': ['Quad set (4x12)'],
        },
      ],
    },
    {
      'category': 'Hamstrings and Calves',
      'icon': Icons.directions_walk,
      'types': [
        {
          'name': 'Hamstring Strain',
          'exercises': ['Isometric contraction (3x10)'],
        },
        {
          'name': 'Calf Strain',
          'exercises': ['Calf Raises (3x15)'],
        },
      ],
    },
    {
      'category': 'Core',
      'icon': Icons.accessibility,
      'types': [
        {
          'name': 'Groin Pull & Adductor Tendinopathy',
          'exercises': ['Isometric hip adduction (3x15)'],
        },
        {
          'name': 'Lumbar Strain & Spondylolysis',
          'exercises': ['Bird-dog (3x10)'],
        },
      ],
    }, // Altre categorie complete...
  ];

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 20),
      child: Column(
        children: [
          const Text(
            'Select Injury Type',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          Expanded(
            child: ListView.builder(
              itemCount: _categories.length,
              itemBuilder:
                  (ctx, index) => _CategorySection(
                    category: _categories[index]['category'] as String,
                    icon: _categories[index]['icon'] as IconData,
                    types: _categories[index]['types'] as List<dynamic>,
                    onSelect: onSelect,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CategorySection extends StatelessWidget {
  final String category;
  final IconData icon;
  final List<dynamic> types;
  final Function(Injury) onSelect;

  const _CategorySection({
    required this.category,
    required this.icon,
    required this.types,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(category),
      children:
          types
              .map(
                (type) => ListTile(
                  leading: const Icon(Icons.medical_services),
                  title: Text(type['name']),
                  subtitle: Text(
                    '${(type['exercises'] as List).length} exercises',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  onTap:
                      () => onSelect(
                        Injury(
                          category: category,
                          type: type['name'],
                          exercises: List<String>.from(type['exercises']),
                          date: DateTime.now(),
                        ),
                      ),
                ),
              )
              .toList(),
    );
  }
}

class _InjuryDetails extends StatelessWidget {
  final List<Injury> injuries;
  final Function(int) onRemove;

  const _InjuryDetails({required this.injuries, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Injury Details'),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            onPressed: () => _showHelp(context),
          ),
        ],
      ),
      body:
          injuries.isEmpty
              ? const Center(child: Text('No injuries recorded'))
              : ListView.builder(
                itemCount: injuries.length,
                itemBuilder:
                    (ctx, index) => _InjuryItem(
                      injury: injuries[index],
                      onDelete: () => _confirmDelete(context, index),
                    ),
              ),
    );
  }

  void _confirmDelete(BuildContext context, int index) {
    showDialog(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Confirm Delete'),
            content: const Text('Remove this injury record?'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: () {
                  onRemove(index);
                  Navigator.pop(ctx);
                  Navigator.pop(context);
                },
                child: const Text('Delete'),
              ),
            ],
          ),
    );
  }

  void _showHelp(BuildContext context) {
    showDialog(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Rehabilitation Tips'),
            content: const Text(
              '• Follow medical advice\n'
              '• Progress gradually\n'
              '• Monitor pain levels\n'
              '• Maintain proper form',
            ),
            actions: [
              FilledButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Close'),
              ),
            ],
          ),
    );
  }
}

class _InjuryItem extends StatelessWidget {
  final Injury injury;
  final VoidCallback onDelete;

  const _InjuryItem({required this.injury, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: ExpansionTile(
        leading: const Icon(Icons.medical_information),
        title: Text(injury.type),
        subtitle: Text(injury.category),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline, color: Colors.red),
          onPressed: onDelete,
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Recommended Exercises:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                ...injury.exercises.map((e) => Text('• $e')).toList(),
                const SizedBox(height: 16),
                Row(
                  children: [
                    const Icon(Icons.calendar_month, size: 16),
                    const SizedBox(width: 8),
                    Text('Added: ${_formatDate(injury.date)}'),
                  ],
                ),
                Row(
                  children: [
                    ElevatedButton(
                      onPressed: () {
                        final Map<String, dynamic> myData = {
                          'giocatore': Player,
                        };

                        ApiService.sendData(myData);
                      },
                      child: Text("Invia"),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}

class ApiService {
  static const String address = '192.168.0.105:5010';

  static Future<void> sendData(Map<String, dynamic> data) async {
    final url = Uri.http(address, 'api/data/$data');

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );

    if (response.statusCode != 200) {
      throw Exception('${response.statusCode} - Errore nell’invio dei dati');
    }
  }
}
