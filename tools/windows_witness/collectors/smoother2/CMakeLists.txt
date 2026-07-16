cmake_minimum_required(VERSION 3.20)
project(olm_smoother2_witness LANGUAGES CXX)

if(NOT WIN32)
  message(FATAL_ERROR "This collector is Windows-only")
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

add_executable(olm_injector injector.cpp)
target_compile_definitions(olm_injector PRIVATE UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX)
target_link_libraries(olm_injector PRIVATE Advapi32)

add_library(olm_smoother2_collector SHARED smoother2_collector.cpp)
target_compile_definitions(olm_smoother2_collector PRIVATE UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX)
target_link_libraries(olm_smoother2_collector PRIVATE Advapi32 Bcrypt Psapi)
set_target_properties(olm_smoother2_collector PROPERTIES OUTPUT_NAME "olm_smoother2_collector")
