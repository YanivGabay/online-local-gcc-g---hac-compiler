# Use Rocky Linux 8 as the base image
FROM rockylinux/rockylinux:8

# Install necessary development tools and dependencies
RUN dnf install -y \
    gcc \
    gcc-c++ \
    valgrind \
    && dnf clean all

# Set the working directory inside the container (optional)
WORKDIR /app

# Default command to verify GCC installation
CMD ["gcc", "--version"]
