cmake_minimum_required(VERSION 3.10)
project(IMUReceiver)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Warnings
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")

# Executable
add_executable(imu_receiver imu_receiver.cpp)

# Link threads
find_package(Threads REQUIRED)
target_link_libraries(imu_receiver Threads::Threads)

# Install
install(TARGETS imu_receiver DESTINATION bin)
