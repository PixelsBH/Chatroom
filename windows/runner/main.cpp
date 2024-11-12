#include <flutter/dart_project.h>
#include <flutter/flutter_view_controller.h>
#include <windows.h>
#include <random>
#include <string>
#include <ctime>

#include "flutter_window.h"
#include "utils.h"

int APIENTRY wWinMain(_In_ HINSTANCE instance, _In_opt_ HINSTANCE prev,
                      _In_ wchar_t *command_line, _In_ int show_command) {
  // Initialize random seed
  srand(static_cast<unsigned>(time(nullptr)) + GetCurrentProcessId());
  
  // Generate random position and title
  int randX = rand() % 300;  // Random X position
  int randY = rand() % 200;  // Random Y position
  std::wstring window_title = L"Chat App " + std::to_wstring(GetCurrentProcessId());

  // Initialize COM
  ::CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);

  flutter::DartProject project(L"data");
  std::vector<std::string> command_line_arguments =
      GetCommandLineArguments();

  project.set_dart_entrypoint_arguments(std::move(command_line_arguments));

  FlutterWindow window(project);
  Win32Window::Point origin(randX, randY);  // Random starting position
  Win32Window::Size size(800, 600);

  if (!window.Create(window_title.c_str(), origin, size)) {
    return EXIT_FAILURE;
  }
  window.SetQuitOnClose(true);

  ::MSG msg;
  while (::GetMessage(&msg, nullptr, 0, 0)) {
    ::TranslateMessage(&msg);
    ::DispatchMessage(&msg);
  }

  ::CoUninitialize();
  return EXIT_SUCCESS;
} 