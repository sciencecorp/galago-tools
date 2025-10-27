import socket
import grpc
import concurrent.futures
import time
import os
import datetime
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc

def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Quick check if a TCP port is open on the host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except Exception:
            return False

def check_grpc_reflection(host: str, port: int) -> bool:
    """
    Attempt to call the gRPC reflection API.
    
    Returns True if the server responds to a reflection request.
    Note: The server must have reflection enabled.
    """
    target = f"{host}:{port}"
    channel = grpc.insecure_channel(target)
    stub = reflection_pb2_grpc.ServerReflectionStub(channel)
    request = reflection_pb2.ServerReflectionRequest(list_services="")

    try:
        responses = stub.ServerReflectionInfo(iter([request]))
        for response in responses:
            if response.HasField("list_services_response"):
                return True
    except Exception:
        return False
    finally:
        channel.close()  # Ensure the channel is closed after use.
    return False

def discover_grpc_servers(host: str, start_port: int, end_port: int) -> list[int]:
    """
    Scan a range of ports on the given host.
    
    Returns a list of ports where a gRPC server (with reflection enabled)
    was detected.
    """
    found_ports = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_port = {}
        for port in range(start_port, end_port + 1):
            if is_port_open(host, port):
                # Submit the reflection check for this open port.
                future = executor.submit(check_grpc_reflection, host, port)
                future_to_port[future] = port

        for future in concurrent.futures.as_completed(future_to_port):
            port = future_to_port[future]
            try:
                if future.result():
                    found_ports.append(port)
            except Exception:
                pass
    return found_ports

def main() -> int:
    host = "localhost"
    # the scanning range is defined on db service.
    start_port = 4000
    end_port = 5000
    hardcoded_port = 1010  # for tool box

    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"==== Galago Tools gRPC Server Discovery at {timestamp} ====\n")
            print(f"Scanning {host} ports {start_port} to {end_port} for gRPC servers...\n")
            
            discovered_ports = set(discover_grpc_servers(host, start_port, end_port))
            if is_port_open(host, hardcoded_port) and check_grpc_reflection(host, hardcoded_port):
                discovered_ports.add(hardcoded_port)
            
            if discovered_ports:
                print("Discovered gRPC servers on the following ports:")
                for port in sorted(discovered_ports):
                    print(f"  - {host}:{port}")
            else:
                print("No active gRPC servers found.")

            print("\nNext scan in 10 seconds. Press Ctrl+C to exit.")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nDiscovery interrupted by user. Exiting gracefully.")
        return 0 
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1

if __name__ == "__main__":
    main()
