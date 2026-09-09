import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const WeatherGPTApp());
}

// ============================================================================
// WEATHERGPT APP
// ============================================================================

class WeatherGPTApp extends StatelessWidget {
  const WeatherGPTApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WeatherGPT',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF07111F),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF38BDF8),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const WeatherGPTHome(),
    );
  }
}

// ============================================================================
// HOME PAGE
// ============================================================================

class WeatherGPTHome extends StatefulWidget {
  const WeatherGPTHome({super.key});

  @override
  State<WeatherGPTHome> createState() => _WeatherGPTHomeState();
}

class _WeatherGPTHomeState extends State<WeatherGPTHome> {
  // ==========================================================================
  // CONTROLLERS
  // ==========================================================================

  final TextEditingController _questionController =
      TextEditingController();

  final TextEditingController _locationController =
      TextEditingController();

  // ==========================================================================
  // BACKEND URLS
  // ==========================================================================

  static const String backendBaseUrl =
      'http://127.0.0.1:8000';

  static const String chatEndpoint =
      '$backendBaseUrl/chat';

  static const String currentEndpoint =
      '$backendBaseUrl/current';

  // ==========================================================================
  // LOCATION STATE
  // ==========================================================================

  String selectedLocation = '';

  bool locationDialogOpen = false;

  final List<String> popularLocations = [
    'Guntur',
    'Vijayawada',
    'Chennai',
    'Hyderabad',
    'Bengaluru',
  ];

  // ==========================================================================
  // LIVE WEATHER STATE
  // ==========================================================================

  bool liveWeatherLoading = false;

  String? liveWeatherError;

  Map<String, dynamic>? liveWeather;

  // ==========================================================================
  // AI STATE
  // ==========================================================================

  bool aiLoading = false;

  String aiAnswer = '';

  String? aiError;

  // ==========================================================================
  // EXAMPLE QUESTIONS
  // ==========================================================================

  final List<String> exampleQuestions = [
    'Can I go running tomorrow?',
    'What will the weather be tomorrow?',
    'What if the temperature is 40 degrees while running?',
    'Is it safe to travel tomorrow?',
  ];

  // ==========================================================================
  // INITIALIZATION
  // ==========================================================================

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      showLocationDialog();
    });
  }

  // ==========================================================================
  // DISPOSE
  // ==========================================================================

  @override
  void dispose() {
    _questionController.dispose();
    _locationController.dispose();

    super.dispose();
  }

  // ==========================================================================
  // LOCATION DIALOG
  // ==========================================================================

  Future<void> showLocationDialog() async {
    if (!mounted || locationDialogOpen) {
      return;
    }

    locationDialogOpen = true;

    _locationController.text = selectedLocation;

    final String? chosenLocation = await showDialog<String>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: const Color(0xFF0D1B2A),
              surfaceTintColor: Colors.transparent,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(24),
              ),
              titlePadding: const EdgeInsets.fromLTRB(
                28,
                28,
                28,
                8,
              ),
              contentPadding: const EdgeInsets.fromLTRB(
                28,
                12,
                28,
                28,
              ),
              title: const Row(
                children: [
                  Icon(
                    Icons.location_on_outlined,
                    color: Color(0xFF38BDF8),
                    size: 28,
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Choose your location',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              content: SizedBox(
                width: 500,
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Select a city to see its live weather conditions and use it as the default location for your weather questions.',
                        style: TextStyle(
                          color: Color(0xFF94A3B8),
                          height: 1.5,
                        ),
                      ),

                      const SizedBox(height: 22),

                      TextField(
                        controller: _locationController,
                        autofocus: true,
                        textInputAction:
                            TextInputAction.search,
                        onChanged: (_) {
                          setDialogState(() {});
                        },
                        onSubmitted: (value) {
                          final location =
                              value.trim();

                          if (location.isNotEmpty) {
                            Navigator.of(
                              dialogContext,
                            ).pop(location);
                          }
                        },
                        decoration: InputDecoration(
                          labelText: 'City or location',
                          hintText: 'e.g. Guntur',
                          prefixIcon: const Icon(
                            Icons.search,
                          ),
                          filled: true,
                          fillColor:
                              const Color(0xFF07111F),
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(14),
                            borderSide:
                                const BorderSide(
                              color: Color(0xFF20354A),
                            ),
                          ),
                          enabledBorder:
                              OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(14),
                            borderSide:
                                const BorderSide(
                              color: Color(0xFF20354A),
                            ),
                          ),
                          focusedBorder:
                              OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(14),
                            borderSide:
                                const BorderSide(
                              color: Color(0xFF38BDF8),
                              width: 1.5,
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 22),

                      const Text(
                        'POPULAR LOCATIONS',
                        style: TextStyle(
                          color: Color(0xFF64748B),
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.1,
                        ),
                      ),

                      const SizedBox(height: 12),

                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children:
                            popularLocations.map(
                          (location) {
                            final isSelected =
                                _locationController
                                        .text
                                        .trim()
                                        .toLowerCase() ==
                                    location
                                        .toLowerCase();

                            return ActionChip(
                              label: Text(location),
                              avatar: Icon(
                                Icons.location_city,
                                size: 16,
                                color: isSelected
                                    ? const Color(
                                        0xFF38BDF8,
                                      )
                                    : const Color(
                                        0xFF94A3B8,
                                      ),
                              ),
                              onPressed: () {
                                _locationController
                                    .text = location;

                                setDialogState(() {});
                              },
                              backgroundColor:
                                  const Color(0xFF07111F),
                              side: BorderSide(
                                color: isSelected
                                    ? const Color(
                                        0xFF38BDF8,
                                      )
                                    : const Color(
                                        0xFF20354A,
                                      ),
                              ),
                              labelStyle: TextStyle(
                                color: isSelected
                                    ? const Color(
                                        0xFF7DD3FC,
                                      )
                                    : const Color(
                                        0xFFCBD5E1,
                                      ),
                              ),
                            );
                          },
                        ).toList(),
                      ),

                      const SizedBox(height: 25),

                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: FilledButton.icon(
                          onPressed: () {
                            final location =
                                _locationController
                                    .text
                                    .trim();

                            if (location.isNotEmpty) {
                              Navigator.of(
                                dialogContext,
                              ).pop(location);
                            }
                          },
                          icon: const Icon(
                            Icons.check,
                          ),
                          label: const Text(
                            'Show Live Weather',
                          ),
                          style: FilledButton.styleFrom(
                            shape:
                                RoundedRectangleBorder(
                              borderRadius:
                                  BorderRadius.circular(
                                13,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );

    locationDialogOpen = false;

    if (!mounted) {
      return;
    }

    if (chosenLocation != null &&
        chosenLocation.trim().isNotEmpty) {
      setState(() {
        selectedLocation =
            chosenLocation.trim();

        liveWeather = null;
        liveWeatherError = null;
        aiAnswer = '';
        aiError = null;
      });

      await loadLiveWeather();
    }
  }

  // ==========================================================================
  // LOAD LIVE WEATHER
  // ==========================================================================

  Future<void> loadLiveWeather() async {
    if (selectedLocation.isEmpty) {
      return;
    }

    setState(() {
      liveWeatherLoading = true;
      liveWeatherError = null;
    });

    try {
      final uri = Uri.parse(
        currentEndpoint,
      ).replace(
        queryParameters: {
          'location': selectedLocation,
        },
      );

      final response = await http
          .get(uri)
          .timeout(
            const Duration(seconds: 15),
          );

      if (!mounted) {
        return;
      }

      if (response.statusCode == 200) {
        final decoded =
            jsonDecode(response.body);

        if (decoded is Map<String, dynamic>) {
          setState(() {
            liveWeather = decoded;
            liveWeatherLoading = false;
          });
        } else {
          setState(() {
            liveWeatherError =
                'Invalid weather data received from the backend.';
            liveWeatherLoading = false;
          });
        }
      } else {
        String message =
            'Unable to load live weather. '
            'HTTP ${response.statusCode}.';

        try {
          final decoded =
              jsonDecode(response.body);

          if (decoded is Map &&
              decoded['detail'] != null) {
            message =
                decoded['detail'].toString();
          }
        } catch (_) {}

        setState(() {
          liveWeatherError = message;
          liveWeatherLoading = false;
        });
      }
    } catch (_) {
      if (!mounted) {
        return;
      }

      setState(() {
        liveWeatherError =
            'Unable to connect to the WeatherGPT backend.';
        liveWeatherLoading = false;
      });
    }
  }

  // ==========================================================================
  // ASK WEATHERGPT
  // ==========================================================================

  Future<void> askWeatherGPT([
    String? suppliedQuestion,
  ]) async {
    final question =
        (suppliedQuestion ??
                _questionController.text)
            .trim();

    if (question.isEmpty) {
      setState(() {
        aiError =
            'Please enter a weather question.';
      });

      return;
    }

    setState(() {
      aiLoading = true;
      aiError = null;
      aiAnswer = '';
    });

    try {
      final response = await http
          .post(
            Uri.parse(chatEndpoint),
            headers: {
              'Content-Type': 'application/json',
            },
            body: jsonEncode({
              'question': question,
            }),
          )
          .timeout(
            const Duration(seconds: 30),
          );

      if (!mounted) {
        return;
      }

      if (response.statusCode >= 200 &&
          response.statusCode < 300) {
        final decoded =
            jsonDecode(response.body);

        setState(() {
          aiAnswer =
              decoded['answer']?.toString() ??
                  'No answer received.';
          aiLoading = false;
        });
      } else {
        String message =
            'Backend error: HTTP '
            '${response.statusCode}.';

        try {
          final decoded =
              jsonDecode(response.body);

          if (decoded is Map &&
              decoded['detail'] != null) {
            message =
                decoded['detail'].toString();
          }
        } catch (_) {}

        setState(() {
          aiError = message;
          aiLoading = false;
        });
      }
    } catch (_) {
      if (!mounted) {
        return;
      }

      setState(() {
        aiError =
            'Unable to connect to WeatherGPT.\n\n'
            'Make sure the FastAPI backend is running '
            'at http://127.0.0.1:8000';
        aiLoading = false;
      });
    }
  }

  // ==========================================================================
  // USE EXAMPLE QUESTION
  // ==========================================================================

  void useExample(String question) {
    String finalQuestion = question;

    if (selectedLocation.isNotEmpty) {
      final trimmed =
          question.trim();

      if (trimmed.endsWith('?')) {
        finalQuestion =
            '${trimmed.substring(0, trimmed.length - 1)} '
            'in $selectedLocation?';
      } else {
        finalQuestion =
            '$trimmed in $selectedLocation';
      }
    }

    _questionController.text =
        finalQuestion;

    askWeatherGPT(finalQuestion);
  }

  // ==========================================================================
  // MAIN BUILD
  // ==========================================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(
            horizontal: 24,
            vertical: 28,
          ),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxWidth: 1150,
              ),
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  buildHeader(),

                  const SizedBox(height: 60),

                  buildHero(),

                  const SizedBox(height: 32),

                  buildLiveWeather(),

                  const SizedBox(height: 32),

                  buildSearch(),

                  const SizedBox(height: 18),

                  buildExamples(),

                  if (aiLoading) ...[
                    const SizedBox(height: 30),
                    buildLoading(),
                  ],

                  if (aiError != null) ...[
                    const SizedBox(height: 25),
                    buildError(),
                  ],

                  if (aiAnswer.isNotEmpty &&
                      !aiLoading) ...[
                    const SizedBox(height: 35),
                    buildResults(),
                  ],

                  const SizedBox(height: 50),

                  buildFooter(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ==========================================================================
  // HEADER
  // ==========================================================================

  Widget buildHeader() {
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            borderRadius:
                BorderRadius.circular(14),
            gradient: const LinearGradient(
              colors: [
                Color(0xFF38BDF8),
                Color(0xFF6366F1),
              ],
            ),
          ),
          child: const Icon(
            Icons.cloud,
            color: Colors.white,
            size: 27,
          ),
        ),

        const SizedBox(width: 14),

        const Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            Text(
              'WeatherGPT',
              style: TextStyle(
                fontSize: 21,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              'AI Weather Decision Support',
              style: TextStyle(
                color: Color(0xFF94A3B8),
                fontSize: 12,
              ),
            ),
          ],
        ),

        const Spacer(),

        if (selectedLocation.isNotEmpty)
          InkWell(
            onTap: showLocationDialog,
            borderRadius:
                BorderRadius.circular(20),
            child: Container(
              padding:
                  const EdgeInsets.symmetric(
                horizontal: 13,
                vertical: 8,
              ),
              decoration: BoxDecoration(
                color: const Color(0xFF0D1B2A),
                borderRadius:
                    BorderRadius.circular(20),
                border: Border.all(
                  color: const Color(0xFF20354A),
                ),
              ),
              child: Row(
                mainAxisSize:
                    MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.location_on_outlined,
                    color: Color(0xFF38BDF8),
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    selectedLocation,
                    style: const TextStyle(
                      color: Color(0xFFCBD5E1),
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(width: 5),
                  const Icon(
                    Icons.keyboard_arrow_down,
                    color: Color(0xFF64748B),
                    size: 16,
                  ),
                ],
              ),
            ),
          ),

        if (selectedLocation.isNotEmpty)
          const SizedBox(width: 10),

        Container(
          padding:
              const EdgeInsets.symmetric(
            horizontal: 13,
            vertical: 8,
          ),
          decoration: BoxDecoration(
            color: const Color(0xFF0D1B2A),
            borderRadius:
                BorderRadius.circular(20),
            border: Border.all(
              color: const Color(0xFF20354A),
            ),
          ),
          child: const Row(
            mainAxisSize:
                MainAxisSize.min,
            children: [
              Icon(
                Icons.circle,
                color: Color(0xFF4ADE80),
                size: 8,
              ),
              SizedBox(width: 7),
              Text(
                'AI Engine Online',
                style: TextStyle(
                  color: Color(0xFFCBD5E1),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ==========================================================================
  // HERO
  // ==========================================================================

  Widget buildHero() {
    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        ShaderMask(
          shaderCallback: (bounds) {
            return const LinearGradient(
              colors: [
                Color(0xFFE0F2FE),
                Color(0xFF38BDF8),
              ],
            ).createShader(bounds);
          },
          child: const Text(
            'Ask the weather.\nGet a decision.',
            style: TextStyle(
              color: Colors.white,
              fontSize: 52,
              height: 1.05,
              fontWeight: FontWeight.w800,
              letterSpacing: -1.5,
            ),
          ),
        ),

        const SizedBox(height: 18),

        const SizedBox(
          width: 800,
          child: Text(
            'WeatherGPT combines live weather data, '
            'risk analysis, activity-aware decisions, '
            'forecast confidence and AI explanations '
            'to help you decide what to do.',
            style: TextStyle(
              color: Color(0xFF94A3B8),
              fontSize: 17,
              height: 1.6,
            ),
          ),
        ),
      ],
    );
  }

  // ==========================================================================
  // LIVE WEATHER CARD
  // ==========================================================================

  Widget buildLiveWeather() {
    if (selectedLocation.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(25),
        decoration: BoxDecoration(
          color: const Color(0xFF0D1B2A),
          borderRadius:
              BorderRadius.circular(20),
          border: Border.all(
            color: const Color(0xFF20354A),
          ),
        ),
        child: Row(
          children: [
            const Icon(
              Icons.location_on_outlined,
              color: Color(0xFF38BDF8),
              size: 27,
            ),

            const SizedBox(width: 12),

            const Expanded(
              child: Text(
                'Choose a location to see live weather.',
                style: TextStyle(
                  color: Color(0xFFCBD5E1),
                  fontSize: 15,
                ),
              ),
            ),

            FilledButton(
              onPressed: showLocationDialog,
              child: const Text(
                'Choose Location',
              ),
            ),
          ],
        ),
      );
    }

    if (liveWeatherLoading) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(25),
        decoration: BoxDecoration(
          color: const Color(0xFF0D1B2A),
          borderRadius:
              BorderRadius.circular(20),
          border: Border.all(
            color: const Color(0xFF20354A),
          ),
        ),
        child: Row(
          children: [
            const SizedBox(
              width: 23,
              height: 23,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
              ),
            ),

            const SizedBox(width: 15),

            Expanded(
              child: Text(
                'Loading live weather for '
                '$selectedLocation...',
                style: const TextStyle(
                  color: Color(0xFFCBD5E1),
                ),
              ),
            ),
          ],
        ),
      );
    }

    if (liveWeatherError != null) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: const Color(0xFF32151B),
          borderRadius:
              BorderRadius.circular(18),
          border: Border.all(
            color: const Color(0xFF7F1D1D),
          ),
        ),
        child: Row(
          children: [
            const Icon(
              Icons.error_outline,
              color: Color(0xFFF87171),
            ),

            const SizedBox(width: 12),

            Expanded(
              child: Text(
                liveWeatherError!,
                style: const TextStyle(
                  color: Color(0xFFFCA5A5),
                  height: 1.5,
                ),
              ),
            ),

            TextButton.icon(
              onPressed: showLocationDialog,
              icon: const Icon(
                Icons.location_on_outlined,
              ),
              label: const Text(
                'Change',
              ),
            ),

            IconButton(
              onPressed: loadLiveWeather,
              icon: const Icon(
                Icons.refresh,
              ),
              tooltip: 'Retry',
            ),
          ],
        ),
      );
    }

    if (liveWeather == null) {
      return const SizedBox.shrink();
    }

    final weather = liveWeather!;

    final temperature =
        weather['temperature'];

    final feelsLike =
        weather['feels_like'];

    final humidity =
        weather['humidity'];

    final wind =
        weather['wind_speed'];

    final precipitation =
        weather['precipitation'];

    final condition =
        weather['condition']?.toString() ??
            'Unknown';

    final location =
        weather['location']?.toString() ??
            selectedLocation;

    final time =
        weather['time']?.toString() ??
            '';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(25),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFF102B45),
            Color(0xFF0D1B2A),
          ],
        ),
        borderRadius:
            BorderRadius.circular(22),
        border: Border.all(
          color: const Color(0xFF28506D),
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x33000000),
            blurRadius: 25,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          // --------------------------------------------------------------
          // LIVE WEATHER HEADER
          // --------------------------------------------------------------

          Row(
            children: [
              const Icon(
                Icons.my_location,
                color: Color(0xFF4ADE80),
                size: 17,
              ),

              const SizedBox(width: 8),

              const Text(
                'LIVE WEATHER',
                style: TextStyle(
                  color: Color(0xFF4ADE80),
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                ),
              ),

              const Spacer(),

              TextButton.icon(
                onPressed: showLocationDialog,
                icon: const Icon(
                  Icons.location_on_outlined,
                  size: 16,
                ),
                label: const Text(
                  'Change',
                ),
                style: TextButton.styleFrom(
                  foregroundColor:
                      const Color(0xFF94A3B8),
                ),
              ),

              IconButton(
                onPressed: loadLiveWeather,
                icon: const Icon(
                  Icons.refresh,
                  color: Color(0xFF94A3B8),
                ),
                tooltip: 'Refresh weather',
              ),
            ],
          ),

          const SizedBox(height: 8),

          // --------------------------------------------------------------
          // LOCATION
          // --------------------------------------------------------------

          Row(
            children: [
              const Icon(
                Icons.location_on_outlined,
                color: Color(0xFF38BDF8),
                size: 22,
              ),

              const SizedBox(width: 7),

              Expanded(
                child: Text(
                  location,
                  style: const TextStyle(
                    fontSize: 21,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 25),

          // --------------------------------------------------------------
          // TEMPERATURE
          // --------------------------------------------------------------

          Row(
            crossAxisAlignment:
                CrossAxisAlignment.center,
            children: [
              Icon(
                liveWeatherIcon(
                  condition,
                ),
                color:
                    const Color(0xFF7DD3FC),
                size: 62,
              ),

              const SizedBox(width: 18),

              Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  Text(
                    '${formatNumber(temperature)}°C',
                    style: const TextStyle(
                      fontSize: 43,
                      fontWeight:
                          FontWeight.w800,
                    ),
                  ),

                  Text(
                    condition,
                    style: const TextStyle(
                      color: Color(0xFFCBD5E1),
                      fontSize: 15,
                    ),
                  ),

                  const SizedBox(height: 5),

                  Text(
                    'Feels like '
                    '${formatNumber(feelsLike)}°C',
                    style: const TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 25),

          // --------------------------------------------------------------
          // LIVE METRICS
          // --------------------------------------------------------------

          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              buildLiveMetric(
                Icons.water_drop_outlined,
                'Humidity',
                '${formatNumber(humidity)}%',
              ),

              buildLiveMetric(
                Icons.air,
                'Wind',
                '${formatNumber(wind)} km/h',
              ),

              buildLiveMetric(
                Icons.cloud_outlined,
                'Precipitation',
                '${formatNumber(precipitation)} mm',
              ),
            ],
          ),

          const SizedBox(height: 15),

          Row(
            children: [
              const Icon(
                Icons.update,
                size: 14,
                color: Color(0xFF64748B),
              ),

              const SizedBox(width: 6),

              Text(
                time.isNotEmpty
                    ? 'Updated: '
                        '${formatWeatherTime(time)}'
                    : 'Live data from Open-Meteo',
                style: const TextStyle(
                  color: Color(0xFF64748B),
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // LIVE WEATHER METRIC
  // ==========================================================================

  Widget buildLiveMetric(
    IconData icon,
    String title,
    String value,
  ) {
    return Container(
      width: 180,
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: const Color(0x44071B2E),
        borderRadius:
            BorderRadius.circular(14),
        border: Border.all(
          color: const Color(0x332F6685),
        ),
      ),
      child: Row(
        children: [
          Icon(
            icon,
            color: const Color(0xFF7DD3FC),
            size: 22,
          ),

          const SizedBox(width: 10),

          Column(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 11,
                ),
              ),

              const SizedBox(height: 3),

              Text(
                value,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight:
                      FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // SEARCH BOX
  // ==========================================================================

  Widget buildSearch() {
    return Container(
      padding: const EdgeInsets.all(7),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1B2A),
        borderRadius:
            BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFF20354A),
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x44000000),
            blurRadius: 30,
            offset: Offset(0, 12),
          ),
        ],
      ),
      child: Row(
        children: [
          const SizedBox(width: 15),

          const Icon(
            Icons.search,
            color: Color(0xFF64748B),
          ),

          const SizedBox(width: 12),

          Expanded(
            child: TextField(
              controller:
                  _questionController,
              maxLines: 3,
              minLines: 1,
              onSubmitted: (_) {
                askWeatherGPT();
              },
              style: const TextStyle(
                color: Colors.white,
                fontSize: 15,
              ),
              decoration: InputDecoration(
                hintText: selectedLocation
                    .isEmpty
                    ? 'Ask a weather question...'
                    : 'Ask about '
                        '$selectedLocation...',
                hintStyle:
                    const TextStyle(
                  color: Color(0xFF64748B),
                ),
                border:
                    InputBorder.none,
              ),
            ),
          ),

          const SizedBox(width: 8),

          SizedBox(
            height: 50,
            child: FilledButton.icon(
              onPressed: aiLoading
                  ? null
                  : () => askWeatherGPT(),
              icon: aiLoading
                  ? const SizedBox(
                      width: 17,
                      height: 17,
                      child:
                          CircularProgressIndicator(
                        strokeWidth: 2,
                      ),
                    )
                  : const Icon(
                      Icons.arrow_upward,
                    ),
              label: const Text(
                'Ask',
              ),
              style:
                  FilledButton.styleFrom(
                padding:
                    const EdgeInsets.symmetric(
                  horizontal: 20,
                ),
                shape:
                    RoundedRectangleBorder(
                  borderRadius:
                      BorderRadius.circular(
                    13,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // EXAMPLE QUESTIONS
  // ==========================================================================

  Widget buildExamples() {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children:
          exampleQuestions.map(
        (question) {
          return ActionChip(
            label: Text(question),
            onPressed: aiLoading
                ? null
                : () =>
                    useExample(question),
            backgroundColor:
                const Color(0xFF0D1B2A),
            side: const BorderSide(
              color: Color(0xFF1E334A),
            ),
            labelStyle:
                const TextStyle(
              color: Color(0xFFCBD5E1),
              fontSize: 12,
            ),
          );
        },
      ).toList(),
    );
  }

  // ==========================================================================
  // AI LOADING
  // ==========================================================================

  Widget buildLoading() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1B2A),
        borderRadius:
            BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFF20354A),
        ),
      ),
      child: const Row(
        children: [
          CircularProgressIndicator(),

          SizedBox(width: 18),

          Expanded(
            child: Text(
              'Analyzing weather conditions...',
              style: TextStyle(
                color: Color(0xFFCBD5E1),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // AI ERROR
  // ==========================================================================

  Widget buildError() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF32151B),
        borderRadius:
            BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFF7F1D1D),
        ),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.error_outline,
            color: Color(0xFFF87171),
          ),

          const SizedBox(width: 12),

          Expanded(
            child: Text(
              aiError!,
              style: const TextStyle(
                color: Color(0xFFFCA5A5),
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // AI RESULTS
  // ==========================================================================

  Widget buildResults() {
    final parsed =
        parseAnswer(aiAnswer);

    final weather =
        parseWeather(parsed.forecast);

    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        const Text(
          'WeatherGPT Analysis',
          style: TextStyle(
            fontSize: 27,
            fontWeight: FontWeight.bold,
          ),
        ),

        const SizedBox(height: 20),

        if (weather.hasWeather)
          buildWeatherCard(weather),

        if (parsed.confidence.isNotEmpty)
          buildConfidence(
            parsed.confidence,
          ),

        if (parsed.risk.isNotEmpty)
          buildRisk(
            parsed.risk,
          ),

        if (parsed.decision.isNotEmpty)
          buildDecision(
            parsed.decision,
          ),

        if (parsed.recommendations
            .isNotEmpty)
          buildCard(
            Icons.lightbulb_outline,
            'Recommendations',
            parsed.recommendations,
          ),

        if (parsed.hypothetical
            .isNotEmpty)
          buildCard(
            Icons.science_outlined,
            'What-If Scenario',
            parsed.hypothetical,
          ),

        const SizedBox(height: 15),

        ExpansionTile(
          title: const Text(
            'View complete AI response',
            style: TextStyle(
              fontWeight: FontWeight.w600,
            ),
          ),
          children: [
            Container(
              width: double.infinity,
              padding:
                  const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF0B1726),
                borderRadius:
                    BorderRadius.circular(14),
              ),
              child: SelectableText(
                aiAnswer,
                style: const TextStyle(
                  color: Color(0xFFCBD5E1),
                  height: 1.6,
                  fontSize: 13,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ==========================================================================
  // FORECAST WEATHER CARD
  // ==========================================================================

  Widget buildWeatherCard(
    WeatherData weather,
  ) {
    return Container(
      width: double.infinity,
      margin:
          const EdgeInsets.only(bottom: 15),
      padding:
          const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFF102B45),
            Color(0xFF0D1B2A),
          ],
        ),
        borderRadius:
            BorderRadius.circular(22),
        border: Border.all(
          color: const Color(0xFF28506D),
        ),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.location_on_outlined,
                color: Color(0xFF38BDF8),
                size: 22,
              ),

              const SizedBox(width: 8),

              Expanded(
                child: Text(
                  weather.location,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight:
                        FontWeight.bold,
                  ),
                ),
              ),

              Text(
                weather.date,
                style: const TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 13,
                ),
              ),
            ],
          ),

          const SizedBox(height: 24),

          Row(
            crossAxisAlignment:
                CrossAxisAlignment.center,
            children: [
              Icon(
                weather.icon,
                color:
                    const Color(0xFF7DD3FC),
                size: 58,
              ),

              const SizedBox(width: 18),

              Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  Text(
                    '${weather.high}°C',
                    style: const TextStyle(
                      fontSize: 42,
                      fontWeight:
                          FontWeight.w800,
                    ),
                  ),

                  Text(
                    weather.condition,
                    style: const TextStyle(
                      color: Color(0xFFCBD5E1),
                      fontSize: 15,
                    ),
                  ),

                  const SizedBox(height: 4),

                  Text(
                    'Low ${weather.low}°C',
                    style: const TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 25),

          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              buildWeatherMetric(
                Icons.water_drop_outlined,
                'Rain',
                '${weather.rain}%',
              ),

              buildWeatherMetric(
                Icons.air,
                'Wind',
                '${weather.wind} km/h',
              ),

              buildWeatherMetric(
                Icons.water_outlined,
                'Humidity',
                '${weather.humidity}%',
              ),

              buildWeatherMetric(
                Icons.cloud_outlined,
                'Precipitation',
                '${weather.precipitation} mm',
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // FORECAST METRIC
  // ==========================================================================

  Widget buildWeatherMetric(
    IconData icon,
    String title,
    String value,
  ) {
    return Container(
      width: 175,
      padding:
          const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: const Color(0x44071B2E),
        borderRadius:
            BorderRadius.circular(14),
        border: Border.all(
          color: const Color(0x332F6685),
        ),
      ),
      child: Row(
        children: [
          Icon(
            icon,
            color:
                const Color(0xFF7DD3FC),
            size: 22,
          ),

          const SizedBox(width: 10),

          Column(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 11,
                ),
              ),

              const SizedBox(height: 3),

              Text(
                value,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight:
                      FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // FORECAST CONFIDENCE
  // ==========================================================================

  Widget buildConfidence(
    String confidence,
  ) {
    return Container(
      width: double.infinity,
      margin:
          const EdgeInsets.only(bottom: 15),
      padding:
          const EdgeInsets.all(21),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1B2A),
        borderRadius:
            BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFF1E334A),
        ),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.verified_outlined,
            color: Color(0xFF4ADE80),
            size: 29,
          ),

          const SizedBox(width: 15),

          Column(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              const Text(
                'FORECAST CONFIDENCE',
                style: TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 11,
                  letterSpacing: 1.1,
                  fontWeight:
                      FontWeight.bold,
                ),
              ),

              const SizedBox(height: 5),

              Text(
                confidence,
                style: const TextStyle(
                  fontSize: 21,
                  fontWeight:
                      FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // RISK
  // ==========================================================================

  Widget buildRisk(
    String risk,
  ) {
    final lower =
        risk.toLowerCase();

    Color accent =
        const Color(0xFF4ADE80);

    IconData icon =
        Icons.check_circle_outline;

    if (lower.contains('extreme')) {
      accent =
          const Color(0xFFF87171);
      icon =
          Icons.dangerous_outlined;
    } else if (lower.contains('high')) {
      accent =
          const Color(0xFFFBBF24);
      icon =
          Icons.warning_amber_rounded;
    } else if (lower.contains(
        'moderate')) {
      accent =
          const Color(0xFFFBBF24);
      icon =
          Icons.warning_amber_outlined;
    }

    return Container(
      width: double.infinity,
      margin:
          const EdgeInsets.only(bottom: 15),
      padding:
          const EdgeInsets.all(21),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1B2A),
        borderRadius:
            BorderRadius.circular(18),
        border: Border.all(
          color: accent.withValues(
            alpha: 0.55,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                color: accent,
                size: 27,
              ),

              const SizedBox(width: 10),

              const Text(
                'RISK ASSESSMENT',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight:
                      FontWeight.bold,
                ),
              ),
            ],
          ),

          const SizedBox(height: 15),

          SelectableText(
            risk,
            style: TextStyle(
              color: accent,
              height: 1.65,
              fontSize: 14,
              fontWeight:
                  FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // ACTIVITY DECISION
  // ==========================================================================

  Widget buildDecision(
    String decision,
  ) {
    final lower =
        decision.toLowerCase();

    Color accent =
        const Color(0xFF38BDF8);

    IconData icon =
        Icons.info_outline;

    if (lower.contains('avoid')) {
      accent =
          const Color(0xFFF87171);
      icon = Icons.block;
    } else if (lower.contains(
        'postpone')) {
      accent =
          const Color(0xFFFBBF24);
      icon = Icons.schedule;
    } else if (lower.contains(
        'caution')) {
      accent =
          const Color(0xFFFBBF24);
      icon =
          Icons.warning_amber;
    } else if (lower.contains(
        'proceed')) {
      accent =
          const Color(0xFF4ADE80);
      icon =
          Icons.check_circle_outline;
    }

    return Container(
      width: double.infinity,
      margin:
          const EdgeInsets.only(bottom: 15),
      padding:
          const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: const Color(0xFF101D2D),
        borderRadius:
            BorderRadius.circular(18),
        border: Border.all(
          color: accent.withValues(
            alpha: 0.6,
          ),
          width: 1.5,
        ),
      ),
      child: Row(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Icon(
            icon,
            color: accent,
            size: 32,
          ),

          const SizedBox(width: 15),

          Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                const Text(
                  'ACTIVITY DECISION',
                  style: TextStyle(
                    color: Color(0xFF94A3B8),
                    fontSize: 11,
                    letterSpacing: 1.2,
                    fontWeight:
                        FontWeight.bold,
                  ),
                ),

                const SizedBox(height: 8),

                SelectableText(
                  decision,
                  style: TextStyle(
                    color: accent,
                    fontSize: 16,
                    height: 1.5,
                    fontWeight:
                        FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // GENERAL CARD
  // ==========================================================================

  Widget buildCard(
    IconData icon,
    String title,
    String content,
  ) {
    return Container(
      width: double.infinity,
      margin:
          const EdgeInsets.only(bottom: 15),
      padding:
          const EdgeInsets.all(21),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1B2A),
        borderRadius:
            BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFF1E334A),
        ),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                color:
                    const Color(0xFF38BDF8),
              ),

              const SizedBox(width: 10),

              Text(
                title,
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight:
                      FontWeight.bold,
                ),
              ),
            ],
          ),

          const SizedBox(height: 15),

          SelectableText(
            content,
            style: const TextStyle(
              color: Color(0xFFCBD5E1),
              height: 1.65,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================================================
  // FOOTER
  // ==========================================================================

  Widget buildFooter() {
    return const Center(
      child: Text(
        'Weather risk and activity decisions are calculated by deterministic analysis engines.',
        textAlign: TextAlign.center,
        style: TextStyle(
          color: Color(0xFF64748B),
          fontSize: 12,
        ),
      ),
    );
  }

  // ==========================================================================
  // PARSE AI RESPONSE
  // ==========================================================================

  ParsedAnswer parseAnswer(
    String text,
  ) {
    final parsed =
        ParsedAnswer();

    String section = '';

    for (final raw in text.split('\n')) {
      final line = raw.trim();

      if (line.isEmpty ||
          line == 'WeatherGPT Analysis') {
        continue;
      }

      final lower =
          line.toLowerCase();

      if (lower.startsWith(
          'forecast for')) {
        section = 'forecast';
        parsed.forecast = line;
        continue;
      }

      if (lower.startsWith(
          'forecast confidence:')) {
        section = 'confidence';

        parsed.confidence =
            line.replaceFirst(
          RegExp(
            r'forecast confidence:',
            caseSensitive: false,
          ),
          '',
        ).trim();

        continue;
      }

      if (lower ==
          'risk assessment:') {
        section = 'risk';
        continue;
      }

      if (lower == 'decision:') {
        section = 'decision';
        continue;
      }

      if (lower ==
          'risk recommendations:') {
        section =
            'recommendations';
        continue;
      }

      if (lower ==
          'hypothetical weather scenario:') {
        section = 'hypothetical';
        continue;
      }

      if (lower.startsWith(
          'note:')) {
        section = '';
        continue;
      }

      if (section == 'forecast') {
        parsed.forecast =
            '${parsed.forecast}\n$line';
      } else if (section == 'risk') {
        parsed.risk =
            '${parsed.risk}$line\n';
      } else if (section ==
          'decision') {
        parsed.decision =
            '${parsed.decision}$line\n';
      } else if (section ==
          'recommendations') {
        parsed.recommendations =
            '${parsed.recommendations}$line\n';
      } else if (section ==
          'hypothetical') {
        parsed.hypothetical =
            '${parsed.hypothetical}$line\n';
      }
    }

    parsed.risk =
        parsed.risk.trim();

    parsed.decision =
        parsed.decision.trim();

    parsed.recommendations =
        parsed.recommendations.trim();

    parsed.hypothetical =
        parsed.hypothetical.trim();

    return parsed;
  }

  // ==========================================================================
  // PARSE FORECAST
  // ==========================================================================

  WeatherData parseWeather(
    String forecast,
  ) {
    final weather =
        WeatherData();

    if (forecast.isEmpty) {
      return weather;
    }

    final locationMatch =
        RegExp(
      r'Forecast for (.*?):',
      caseSensitive: false,
    ).firstMatch(forecast);

    if (locationMatch != null) {
      weather.location =
          locationMatch.group(1)!.trim();
    }

    final dateMatch =
        RegExp(
      r'(\d{4}-\d{2}-\d{2}):',
    ).firstMatch(forecast);

    if (dateMatch != null) {
      weather.date =
          dateMatch.group(1)!;
    }

    final conditionMatch =
        RegExp(
      r'\d{4}-\d{2}-\d{2}:\s*([^,]+)',
    ).firstMatch(forecast);

    if (conditionMatch != null) {
      weather.condition =
          conditionMatch.group(1)!.trim();
    }

    final highMatch =
        RegExp(
      r'High\s+([\d.]+)\s*°C',
      caseSensitive: false,
    ).firstMatch(forecast);

    if (highMatch != null) {
      weather.high =
          highMatch.group(1)!;
    }

    final lowMatch =
        RegExp(
      r'Low\s+([\d.]+)\s*°C',
      caseSensitive: false,
    ).firstMatch(forecast);

    if (lowMatch != null) {
      weather.low =
          lowMatch.group(1)!;
    }

    final rainMatch =
        RegExp(
      r'Rain\s+([\d.]+)%',
      caseSensitive: false,
    ).firstMatch(forecast);

    if (rainMatch != null) {
      weather.rain =
          rainMatch.group(1)!;
    }

    final precipitationMatch =
        RegExp(
      r'Precipitation\s+([\d.]+)\s*mm',
      caseSensitive: false,
    ).firstMatch(forecast);

    if (precipitationMatch != null) {
      weather.precipitation =
          precipitationMatch.group(1)!;
    }

    final windMatch =
        RegExp(
      r'Max wind\s+([\d.]+)\s*km/h',
      caseSensitive: false,
    ).firstMatch(forecast);

    if (windMatch != null) {
      weather.wind =
          windMatch.group(1)!;
    }

    final humidityMatch =
        RegExp(
      r'Mean humidity\s+([\d.]+)%',
      caseSensitive: false,
    ).firstMatch(forecast);

    if (humidityMatch != null) {
      weather.humidity =
          humidityMatch.group(1)!;
    }

    return weather;
  }

  // ==========================================================================
  // NUMBER FORMATTER
  // ==========================================================================

  String formatNumber(
    dynamic value,
  ) {
    if (value == null) {
      return '--';
    }

    final number =
        double.tryParse(
      value.toString(),
    );

    if (number == null) {
      return value.toString();
    }

    return number.toStringAsFixed(1);
  }

  // ==========================================================================
  // WEATHER TIME FORMATTER
  // ==========================================================================

  String formatWeatherTime(
    String value,
  ) {
    try {
      final parsed =
          DateTime.parse(value);

      final hour =
          parsed.hour % 12 == 0
              ? 12
              : parsed.hour % 12;

      final minute =
          parsed.minute
              .toString()
              .padLeft(2, '0');

      final period =
          parsed.hour >= 12
              ? 'PM'
              : 'AM';

      return '$hour:$minute $period';
    } catch (_) {
      return value;
    }
  }

  // ==========================================================================
  // LIVE WEATHER ICON
  // ==========================================================================

  IconData liveWeatherIcon(
    String condition,
  ) {
    final text =
        condition.toLowerCase();

    if (text.contains('thunder')) {
      return Icons
          .thunderstorm_outlined;
    }

    if (text.contains('rain') ||
        text.contains('drizzle') ||
        text.contains('shower')) {
      return Icons
          .umbrella_outlined;
    }

    if (text.contains('cloud') ||
        text.contains('overcast')) {
      return Icons
          .cloud_outlined;
    }

    if (text.contains('fog')) {
      return Icons
          .cloud_outlined;
    }

    if (text.contains('snow')) {
      return Icons.ac_unit;
    }

    if (text.contains('clear') ||
        text.contains('sun')) {
      return Icons
          .wb_sunny_outlined;
    }

    return Icons.cloud_outlined;
  }
}

// ============================================================================
// PARSED AI ANSWER MODEL
// ============================================================================

class ParsedAnswer {
  String forecast = '';

  String confidence = '';

  String risk = '';

  String decision = '';

  String recommendations = '';

  String hypothetical = '';
}

// ============================================================================
// FORECAST WEATHER MODEL
// ============================================================================

class WeatherData {
  String location = '';

  String date = '';

  String condition = '';

  String high = '';

  String low = '';

  String rain = '';

  String precipitation = '';

  String wind = '';

  String humidity = '';

  bool get hasWeather =>
      location.isNotEmpty &&
      date.isNotEmpty &&
      high.isNotEmpty;

  IconData get icon {
    final text =
        condition.toLowerCase();

    if (text.contains('thunder')) {
      return Icons
          .thunderstorm_outlined;
    }

    if (text.contains('rain') ||
        text.contains('drizzle') ||
        text.contains('shower')) {
      return Icons
          .umbrella_outlined;
    }

    if (text.contains('cloud')) {
      return Icons
          .cloud_outlined;
    }

    if (text.contains('snow')) {
      return Icons.ac_unit;
    }

    if (text.contains('clear') ||
        text.contains('sun')) {
      return Icons
          .wb_sunny_outlined;
    }

    return Icons.cloud_outlined;
  }
}
