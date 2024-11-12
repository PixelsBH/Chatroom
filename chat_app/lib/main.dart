import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/io.dart';
import 'dart:convert';
import 'dart:async';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Chat App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        brightness: Brightness.dark,
      ),
      home: const LoginScreen(),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isRegistering = false;

  void _handleAuth(BuildContext context) async {
    // Use localhost since we're running on the same machine
    final channel = IOWebSocketChannel.connect('ws://localhost:8765');

    // Convert the stream to a broadcast stream
    final broadcastStream = channel.stream.asBroadcastStream();

    // Send auth request
    channel.sink.add(jsonEncode({
      'action': _isRegistering ? 'register' : 'login',
      'username': _usernameController.text,
      'password': _passwordController.text,
    }));

    // Listen for response
    broadcastStream.listen((message) {
      final response = jsonDecode(message);

      if (response['type'] == 'auth_response') {
        if (response['success']) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => ChatScreen(
                channel: channel,
                stream: broadcastStream,
                username: _usernameController.text,
              ),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(response['message'])),
          );
          channel.sink.close();
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Container(
          width: 300, // Fixed width for login window
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.grey[850],
            borderRadius: BorderRadius.circular(10),
            boxShadow: const [
              BoxShadow(
                color: Colors.black26,
                blurRadius: 10,
                offset: Offset(0, 5),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                _isRegistering ? 'Register' : 'Login',
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _usernameController,
                decoration: InputDecoration(
                  labelText: 'Username',
                  border: const OutlineInputBorder(),
                  filled: true,
                  fillColor: Colors.grey[900],
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _passwordController,
                decoration: InputDecoration(
                  labelText: 'Password',
                  border: const OutlineInputBorder(),
                  filled: true,
                  fillColor: Colors.grey[900],
                ),
                obscureText: true,
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () => _handleAuth(context),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 15),
                  child: Center(
                    child: Text(_isRegistering ? 'Register' : 'Login'),
                  ),
                ),
              ),
              TextButton(
                onPressed: () {
                  setState(() {
                    _isRegistering = !_isRegistering;
                  });
                },
                child: Text(_isRegistering
                    ? 'Already have an account? Login'
                    : 'Need an account? Register'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
}

class ChatScreen extends StatefulWidget {
  final WebSocketChannel channel;
  final Stream stream;
  final String username;

  const ChatScreen(
      {super.key,
      required this.channel,
      required this.stream,
      required this.username});

  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final Map<String, List<String>> _chats = {'global': []};
  List<Map<String, dynamic>> _users = [];
  String _currentChat = 'global';
  StreamSubscription? _subscription;
  final bool _showUserList = false;

  @override
  void initState() {
    super.initState();
    _subscription = widget.stream.listen((message) {
      final data = jsonDecode(message);
      print("Received message type: ${data['type']}"); // Debug print

      if (data['type'] == 'user_list') {
        print("Received users: ${data['users']}"); // Debug print
        setState(() {
          _users = List<Map<String, dynamic>>.from(data['users']);
          
          // Update chat list if current chat user is no longer in users list
          if (_currentChat != 'global' && 
              !_users.any((u) => u['username'] == _currentChat)) {
            _currentChat = 'global';
          }
        });
      } else if (data['type'] == 'message') {
        setState(() {
          String chatKey;
          if (data['chat_type'] == 'global') {
            chatKey = 'global';
          } else {
            // For DMs, use the other user's username as the key
            if (data['username'] == widget.username) {
              // If we're the sender, use the receiver's username
              final receiver = _users.firstWhere(
                (u) => u['id'] == data['receiver_id'],
                orElse: () => {'username': 'Unknown User'},
              );
              chatKey = receiver['username'];
            } else {
              // If we're the receiver, use the sender's username
              chatKey = data['username'];
            }
          }

          if (!_chats.containsKey(chatKey)) {
            _chats[chatKey] = [];
          }

          _chats[chatKey]!.add('${data['username']}: ${data['content']}');
        });

        if (_currentChat == data['username'] ||
            (_currentChat == 'global' && data['chat_type'] == 'global')) {
          _scrollToBottom();
        }
      }
    });
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _controller.dispose();
    _scrollController.dispose();
    widget.channel.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_currentChat == 'global'
            ? 'Global Chat'
            : 'Chat with $_currentChat'),
        actions: [
          // Add DM button
          IconButton(
            icon: const Icon(Icons.message),
            onPressed: () {
              _showDMDialog();
            },
          ),
          TextButton.icon(
            icon: const Icon(Icons.logout, color: Colors.white),
            label: const Text('Logout', style: TextStyle(color: Colors.white)),
            onPressed: () {
              widget.channel.sink.close();
              Navigator.of(context).pushReplacement(
                MaterialPageRoute(builder: (_) => const LoginScreen()),
              );
            },
          ),
        ],
      ),
      body: Row(
        children: [
          // Chat list sidebar
          Container(
            width: 200,
            color: Colors.grey[850],
            child: Column(
              children: [
                ListTile(
                  title: const Text('Global Chat'),
                  selected: _currentChat == 'global',
                  onTap: () => setState(() => _currentChat = 'global'),
                ),
                const Divider(),
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Text(
                    'Online Users',
                    style: TextStyle(
                      color: Colors.grey[400],
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    itemCount: _users.length,
                    itemBuilder: (context, index) {
                      final user = _users[index];
                      if (user['username'] != widget.username) {
                        return ListTile(
                          leading: Icon(
                            Icons.person,
                            color: Colors.green,  // Online indicator
                          ),
                          title: Text(user['username']),
                          selected: _currentChat == user['username'],
                          onTap: () =>
                              setState(() => _currentChat = user['username']),
                        );
                      }
                      return const SizedBox.shrink();
                    },
                  ),
                ),
              ],
            ),
          ),
          // Vertical divider
          const VerticalDivider(width: 1),
          // Chat area
          Expanded(
            child: Column(
              children: [
                Expanded(
                  child: Container(
                    color: Colors.grey[900],
                    child: ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(10),
                      itemCount: _chats[_currentChat]?.length ?? 0,
                      itemBuilder: (context, index) {
                        final message = _chats[_currentChat]?[index];
                        final isCurrentUser =
                            message?.startsWith('${widget.username}:') ?? false;

                        return Align(
                          alignment: isCurrentUser
                              ? Alignment.centerRight
                              : Alignment.centerLeft,
                          child: Container(
                            margin: const EdgeInsets.symmetric(vertical: 5),
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: isCurrentUser
                                  ? Colors.blue
                                  : Colors.grey[800],
                              borderRadius: BorderRadius.circular(15),
                            ),
                            child: Text(
                              message ?? '',
                              style: const TextStyle(color: Colors.white),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
                Container(
                  color: Colors.grey[850],
                  padding: const EdgeInsets.all(8),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        child: Text(
                          widget.username,
                          style: const TextStyle(
                            color: Colors.grey,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ),
                      Expanded(
                        child: TextField(
                          controller: _controller,
                          decoration: InputDecoration(
                            hintText: 'Enter your message...',
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(20),
                            ),
                            filled: true,
                            fillColor: Colors.grey[900],
                            contentPadding: const EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 10,
                            ),
                          ),
                          onSubmitted: (_) => _sendMessage(),
                        ),
                      ),
                      const SizedBox(width: 8),
                      IconButton(
                        icon: const Icon(Icons.send),
                        onPressed: _sendMessage,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _sendMessage() {
    if (_controller.text.isNotEmpty) {
      final receiverId = _currentChat != 'global'
          ? _users.firstWhere(
              (u) => u['username'] == _currentChat,
              orElse: () => {'id': null},
            )['id']
          : null;

      if (_currentChat != 'global' && receiverId == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('User not found')),
        );
        return;
      }

      widget.channel.sink.add(jsonEncode({
        'type': 'message',
        'content': _controller.text,
        'receiver_id': receiverId,
      }));

      setState(() {
        if (!_chats.containsKey(_currentChat)) {
          _chats[_currentChat] = [];
        }
        _chats[_currentChat]!.add('${widget.username}: ${_controller.text}');
      });

      _controller.clear();
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showDMDialog() {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Start New Chat'),
          content: SizedBox(
            width: double.minPositive,
            child: _users.isEmpty 
                ? const Text('Loading users...')
                : ListView.builder(
                    shrinkWrap: true,
                    itemCount: _users.length,
                    itemBuilder: (context, index) {
                      final user = _users[index];
                      // Show all users except current user
                      if (user['username'] != widget.username) {
                        return ListTile(
                          title: Text(user['username']),
                          onTap: () {
                            setState(() {
                              _currentChat = user['username'];
                              if (!_chats.containsKey(_currentChat)) {
                                _chats[_currentChat] = [];
                              }
                            });
                            Navigator.pop(context);
                          },
                        );
                      }
                      return const SizedBox.shrink();
                    },
                  ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
          ],
        );
      },
    );
  }
}
