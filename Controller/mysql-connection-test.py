#!/usr/bin/env python3
"""
MySQL SSH Tunnel Manager

This script creates an SSH tunnel to a remote MySQL server, runs your
MySQL operations, and then closes the tunnel when done.

Requirements:
- Python 3.6+
- sshtunnel package: pip install sshtunnel
- pymysql package: pip install pymysql

Usage:
python mysql_ssh_tunnel.py --config config_file.ini [--command "SQL QUERY"]
"""

import sys
import os
import subprocess
import argparse
import configparser
import pymysql
from sshtunnel import SSHTunnelForwarder


def load_config(config_file):
    """Load configuration from ini file"""
    if not os.path.exists(config_file):
        print(f"Error: Config file '{config_file}' not found.")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_file)

    # Validate required sections and options
    required_sections = ['ssh', 'mysql']
    required_ssh_options = ['hostname', 'username']
    required_mysql_options = ['host', 'user', 'password', 'database']

    for section in required_sections:
        if section not in config:
            print(f"Error: Missing required section '{section}' in config file.")
            sys.exit(1)

    for option in required_ssh_options:
        if option not in config['ssh']:
            print(f"Error: Missing required SSH option '{option}' in config file.")
            sys.exit(1)

    for option in required_mysql_options:
        if option not in config['mysql']:
            print(f"Error: Missing required MySQL option '{option}' in config file.")
            sys.exit(1)

    return config


def create_ssh_tunnel(config):
    """Create SSH tunnel to the MySQL server"""
    ssh_config = config['ssh']
    mysql_config = config['mysql']

    # Get SSH parameters
    ssh_hostname = ssh_config['hostname']
    ssh_username = ssh_config['username']
    ssh_port = int(ssh_config.get('port', 22))
    ssh_pkey = ssh_config.get('private_key', None)
    ssh_password = ssh_config.get('password', None)

    # Get MySQL parameters
    mysql_host = mysql_config.get('host', 'localhost')

    # Handle port with potential comments
    mysql_port_str = mysql_config.get('port', '3306')
    # Strip any comments (anything after #)
    if '#' in mysql_port_str:
        mysql_port_str = mysql_port_str.split('#')[0].strip()
    mysql_port = int(mysql_port_str)

    # Determine authentication method
    if ssh_pkey and os.path.exists(os.path.expanduser(ssh_pkey)):
        ssh_pkey = os.path.expanduser(ssh_pkey)
    elif not ssh_password and not ssh_pkey:
        ssh_pkey = os.path.expanduser('~/.ssh/id_rsa')
        if not os.path.exists(ssh_pkey):
            ssh_pkey = None

    print(f"\n🔑 Creating SSH tunnel to {ssh_username}@{ssh_hostname}:{ssh_port}")

    # Create tunnel
    try:
        tunnel = SSHTunnelForwarder(
            (ssh_hostname, ssh_port),
            ssh_username=ssh_username,
            ssh_pkey=ssh_pkey,
            ssh_password=ssh_password,
            remote_bind_address=(mysql_host, mysql_port),
            local_bind_address=('127.0.0.1', 0)  # Use a random local port
        )

        tunnel.start()
        local_port = tunnel.local_bind_port

        print(f"✅ SSH tunnel established!")
        print(f"🔌 MySQL connection available at 127.0.0.1:{local_port}")

        return tunnel, local_port

    except Exception as e:
        print(f"❌ Failed to create SSH tunnel: {e}")
        sys.exit(1)


def test_mysql_connection(config, local_port):
    """Test the MySQL connection via the SSH tunnel"""
    mysql_config = config['mysql']

    mysql_host = '127.0.0.1'  # Always use local address with tunnel
    mysql_user = mysql_config['user']
    mysql_password = mysql_config['password']
    mysql_database = mysql_config['database']

    print(f"\n🔍 Testing MySQL connection...")
    print(f"   • Host: {mysql_host}")
    print(f"   • Port: {local_port}")
    print(f"   • User: {mysql_user}")
    print(f"   • Database: {mysql_database}")

    try:
        connection = pymysql.connect(
            host=mysql_host,
            port=local_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            connect_timeout=10
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]

            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_count = len(tables)

        print(f"\n✅ MySQL connection successful!")
        print(f"🗄️  MySQL version: {version}")
        print(f"📋 Tables in {mysql_database}: {table_count}")

        connection.close()
        return True

    except pymysql.Error as e:
        print(f"\n❌ MySQL connection failed: {e}")
        return False


def run_command(config, local_port, command):
    """Run a MySQL command via the tunnel"""
    mysql_config = config['mysql']

    # Build mysql command
    mysql_binary = "mysql"
    mysql_user = mysql_config['user']
    mysql_password = mysql_config['password']
    mysql_database = mysql_config['database']

    # Create command with appropriate arguments
    cmd = [
        mysql_binary,
        f"--host=127.0.0.1",
        f"--port={local_port}",
        f"--user={mysql_user}",
        f"--password={mysql_password}",
        f"{mysql_database}"
    ]

    if command:
        cmd.extend(["-e", command])

    try:
        print(f"\n🔄 Running MySQL command...")

        # If no command specified, run interactive mode
        if not command:
            print(f"📝 Starting interactive MySQL session. Type 'exit' to quit.")
            subprocess.run(cmd)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("\n✅ Command executed successfully:")
                print("─" * 50)
                print(result.stdout)
                print("─" * 50)
            else:
                print(f"\n❌ Command execution failed:")
                print("─" * 50)
                print(result.stderr)
                print("─" * 50)

    except Exception as e:
        print(f"\n❌ Failed to run MySQL command: {e}")


def interactive_session(config, local_port):
    """Start an interactive terminal session"""
    print("\n📝 Starting interactive session")
    print("🔍 Type MySQL commands or type 'exit' to quit")
    print("─" * 50)

    mysql_config = config['mysql']

    while True:
        try:
            command = input("mysql> ")
            command = command.strip()

            if command.lower() in ['exit', 'quit', '\\q']:
                print("Exiting interactive session...")
                break

            if not command:
                continue

            # Create connection for each command
            connection = pymysql.connect(
                host='127.0.0.1',
                port=local_port,
                user=mysql_config['user'],
                password=mysql_config['password'],
                database=mysql_config['database']
            )

            try:
                with connection.cursor() as cursor:
                    cursor.execute(command)
                    if command.lower().startswith(('select', 'show', 'describe', 'desc')):
                        results = cursor.fetchall()
                        if cursor.description:
                            columns = [col[0] for col in cursor.description]
                            print(" | ".join(columns))
                            print("─" * (sum(len(c) for c in columns) + len(columns) * 3))
                            for row in results:
                                print(" | ".join(str(cell) for cell in row))
                        else:
                            print("Query returned no columns.")
                    else:
                        connection.commit()
                        print(f"Query OK, {cursor.rowcount} rows affected")
            except pymysql.Error as e:
                print(f"Error: {e}")

            connection.close()

        except KeyboardInterrupt:
            print("\nExiting interactive session...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description='MySQL SSH Tunnel Manager')
    parser.add_argument('--config', required=True, help='Path to the configuration file')
    parser.add_argument('--command', help='Optional MySQL command to run')
    parser.add_argument('--interactive', action='store_true', help='Start an interactive session')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Create SSH tunnel
    tunnel, local_port = create_ssh_tunnel(config)

    try:
        # Test the connection
        if test_mysql_connection(config, local_port):
            if args.interactive:
                interactive_session(config, local_port)
            elif args.command:
                run_command(config, local_port, args.command)
            else:
                print("\n🤔 No command specified and interactive mode not enabled.")
                print("ℹ️  You can:")
                print("   • Re-run with --command \"YOUR SQL QUERY\" to execute a query")
                print("   • Re-run with --interactive to start an interactive session")

                input("\n📢 Press Enter to close the SSH tunnel and exit...")
    finally:
        # Ensure the tunnel is closed
        print("\n🔒 Closing SSH tunnel...")
        tunnel.close()
        print("✅ SSH tunnel closed. Goodbye!")


if __name__ == "__main__":
    main()