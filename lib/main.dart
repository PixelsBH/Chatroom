import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/io.dart';
import 'dart:convert';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

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
  const LoginScreen({Key? key}) : super(key: key);

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isRegistering = false;

  void _handleAuth(BuildContext context) async {
    final channel = IOWebSocketChannel.connect('ws://localhost:8765');
    
    // Send auth request
    channel.sink.add(jsonEncode({
      'action': _isRegistering ? 'register' : 'login',
      'username': _usernameController.text,
      'password': _passwordController.text,
    }));

    // Listen for response
    channel.stream.listen((message) {
      final response = jsonDecode(message);
      
      if (response['type'] == 'auth_response') {
        if (response['success']) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => ChatScreen(
                channel: channel,
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
          width: 300,  // Fixed width for login window
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.grey[850],
            borderRadius: BorderRadius.circular(10),
            boxShadow: [
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
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 20),
              TextField(
                controller: _usernameController,
                decoration: InputDecoration(
                  labelText: 'Username',
                  border: OutlineInputBorder(),
                  filled: true,
                  fillColor: Colors.grey[900],
                ),
              ),
              SizedBox(height: 10),
              TextField(
                controller: _passwordController,
                decoration: InputDecoration(
                  labelText: 'Password',
                  border: OutlineInputBorder(),
                  filled: true,
                  fillColor: Colors.grey[900],
                ),
                obscureText: true,
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: () => _handleAuth(context),
                child: Container(
                  width: double.infinity,
                  padding: EdgeInsets.symmetric(vertical: 15),
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
                child: Text(
                  _isRegistering 
                    ? 'Already have an account? Login' 
                    : 'Need an account? Register'
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ChatScreen extends StatefulWidget {
  final WebSocketChannel channel;
  final String username;

  const ChatScreen({
    Key? key, 
    required this.channel, 
    required this.username
  }) : super(key: key);

  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final Map<String, List<String>> _chats = {
    'global': []
  };
  List<Map<String, dynamic>> _users = [];
  String _currentChat = 'global';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_currentChat == 'global' ? 'Global Chat' : 'Chat with $_currentChat'),
        actions: [
          TextButton.icon(
            icon: Icon(Icons.logout, color: Colors.white),
            label: Text('Logout', style: TextStyle(color: Colors.white)),
            onPressed: () {
              widget.channel.sink.close();
              Navigator.of(context).pushReplacement(
                MaterialPageRoute(builder: (_) => LoginScreen()),
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
                  title: Text('Global Chat'),
                  selected: _currentChat == 'global',
                  onTap: () => setState(() => _currentChat = 'global'),
                ),
                Divider(),
                Expanded(
                  child: ListView.builder(
                    itemCount: _users.length,
                    itemBuilder: (context, index) {
                      final user = _users[index];
                      if (user['username'] != widget.username) {
                        return ListTile(
                          title: Text(user['username']),
                          selected: _currentChat == user['username'],
                          onTap: () => setState(() => _currentChat = user['username']),
                        );
                      }
                      return SizedBox.shrink();
                    },
                  ),
                ),
              ],
            ),
          ),
          // Vertical divider
          VerticalDivider(width: 1),
          // Chat area
          Expanded(
            child: Column(
              children: [
                Expanded(
                  child: Container(
                    color: Colors.grey[900],
                    child: ListView.builder(
                      controller: _scrollController,
                      padding: EdgeInsets.all(10),
                      itemCount: _chats[_currentChat]?.length ?? 0,
                      itemBuilder: (context, index) {
                        final message = _chats[_currentChat]?[index];
                        final isCurrentUser = message?.startsWith('${widget.username}:') ?? false;
                        
                        return Align(
                          alignment: isCurrentUser
                            ? Alignment.centerRight 
                            : Alignment.centerLeft,
                          child: Container(
                            margin: EdgeInsets.symmetric(vertical: 5),
                            padding: EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: isCurrentUser ? Colors.blue : Colors.grey[800],
                              borderRadius: BorderRadius.circular(15),
                            ),
                            child: Text(
                              message ?? '',
                              style: TextStyle(color: Colors.white),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
                Container(
                  color: Colors.grey[850],
                  padding: EdgeInsets.all(8),
                  child: Row(
                    children: [
                      IconButton(
                        icon: Icon(Icons.attach_file),
                        onPressed: () {
                          // TODO: Implement file attachment
                        },
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
                            contentPadding: EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 10,
                            ),
                          ),
                          onSubmitted: (_) => _sendMessage(),
                        ),
                      ),
                      SizedBox(width: 8),
                      IconButton(
                        icon: Icon(Icons.send),
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
          ? _users.firstWhere((u) => u['username'] == _currentChat)['id']
          : null;

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
    Future.delayed(Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void initState() {
    super.initState();
    widget.channel.stream.listen((message) {
      final data = jsonDecode(message);
      
      if (data['type'] == 'user_list') {
        setState(() {
          _users = List<Map<String, dynamic>>.from(data['users']);
        });
      } else if (data['type'] == 'message') {
        setState(() {
          final chatKey = data['chat_type'] == 'global' 
              ? 'global' 
              : data['username'];
          
          if (!_chats.containsKey(chatKey)) {
            _chats[chatKey] = [];
          }
          
          _chats[chatKey]!.add('${data['username']}: ${data['content']}');
        });
        
        final chatKey = data['chat_type'] == 'global' 
            ? 'global' 
            : data['username'];
            
        if (chatKey == _currentChat) {
          _scrollToBottom();
        }
      }
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    widget.channel.sink.close();
    super.dispose();
  }
} 