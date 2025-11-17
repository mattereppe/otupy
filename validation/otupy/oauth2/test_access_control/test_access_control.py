import logging
import os
import otupy as oc2
import json
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
from otupy.oauth2.OAuth2Authenticator import OAuth2Authenticator
import otupy.profiles.slpf as slpf


logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("controller.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True, datefmt='%t'))
logger.addHandler(file_handler)


dirname = os.path.dirname(__file__)
command_path = os.path.join(dirname,"../openc2-commands")
NUM_TESTS = 100

# Test results tracking
test_results = {
    'total_tests': 0,
    'forbidden_commands': 0,
    'authorized_commands': 0,
    'unexpected_responses': 0,
    'errors': 0,
    'correct_predictions': 0,
    'incorrect_predictions': 0
}


def load_json(path):
    cmds_files = [
        os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
    ]
    lst = []
    for f in cmds_files:
        with open(f, 'r') as j:
            lst.append(json.load(j))
    return lst


def classify_command_expectation(cmd):
    """
    Classify if a command should be forbidden or allowed based on your authorization rules.

    Authorized commands from policy file:
    - update, file, slpf
    - query, features:*, slpf
    - allow, 130.0.16.0/20, slpf
    """
    try:
        action = cmd.action if hasattr(cmd, 'action') else str(cmd).split(',')[0].strip()

        # Convert command to string for easier parsing
        cmd_str = str(cmd).lower()

        # Define authorized command patterns
        authorized_patterns = [
            # update, file, slpf
            ('update' in cmd_str and 'file' in cmd_str),

            # query, features:*, slpf
            ('query' in cmd_str),

            # allow, 130.0.16.0/20, slpf
            ('allow' in cmd_str and '130.0.16.0/32' in cmd_str)
        ]

        # Check if command matches any authorized pattern
        if any(authorized_patterns):
            return 'allowed'
        else:
            return 'forbidden'

    except Exception as e:
        logger.warning(f"Could not classify command {cmd}: {e}")
        return 'unknown'


def check_response(cmd, resp, expected=None):
    """Check if the response is as expected and log results."""
    global test_results

    test_results['total_tests'] += 1

    try:
        cmd_str = str(cmd)

        if resp.status == oc2.StatusCode.FORBIDDEN:
            test_results['forbidden_commands'] += 1
            status = "FORBIDDEN (403)"
            if expected == 'forbidden':
                result = "✓ CORRECT"
                result_symbol = "✓"
            elif expected == 'allowed':
                result = "✗ UNEXPECTED - Should be ALLOWED"
                result_symbol = "✗"
            else:
                result = "? UNKNOWN EXPECTATION"
                result_symbol = "?"

        elif resp.status == oc2.StatusCode.OK or resp.status == oc2.StatusCode.INTERNALERROR or resp.status == oc2.StatusCode.NOTIMPLEMENTED:
            test_results['authorized_commands'] += 1
            status = "AUTHORIZED (200)"
            if expected == 'allowed':
                result = "✓ CORRECT"
                result_symbol = "✓"
            elif expected == 'forbidden':
                result = "✗ UNEXPECTED - Should be FORBIDDEN"
                result_symbol = "✗"
            else:
                result = "? UNKNOWN EXPECTATION"
                result_symbol = "?"

        else:
            test_results['unexpected_responses'] += 1
            status = f"UNEXPECTED ({resp.status.value})"
            result = "? UNEXPECTED STATUS CODE"
            result_symbol = "?"

        # Log with more detail
        logger.info(f"{result_symbol} Command: {cmd_str}")
        logger.info(f"  Expected: {expected}, Got: {status}")
        logger.info(f"  Response: {resp.content.get('status_text', 'No message')}")

        # Console output
        # print(f"{result_symbol} {status}")
        # print(f"  Command: {cmd_str}")
        # print(f"  Expected: {expected} | {result}")
        # if resp.content.get('status_text'):
        #     print(f"  Message: {resp.content.get('status_text')}")
        # print()

        return resp.status

    except Exception as e:
        test_results['errors'] += 1
        logger.error(f"Error processing response for command {cmd}: {e}")
        print(f"✗ERROR: {e}")
        return None


def print_test_summary():
    """Print a summary of test results."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests run: {test_results['total_tests']}")
    print(f"Commands forbidden (403): {test_results['forbidden_commands']}")
    print(f"Commands authorized (200+): {test_results['authorized_commands']}")
    print(f"Unexpected responses: {test_results['unexpected_responses']}")
    print(f"Errors: {test_results['errors']}")

    print(f"\nAUTHORIZATION TEST RESULTS:")
    print(f"✓ Correct predictions: {test_results['correct_predictions']}")
    print(f"✗ Incorrect predictions: {test_results['incorrect_predictions']}")

    if test_results['total_tests'] > 0:
        forbidden_rate = (test_results['forbidden_commands'] / test_results['total_tests']) * 100
        authorized_rate = (test_results['authorized_commands'] / test_results['total_tests']) * 100

        total_predictions = test_results['correct_predictions'] + test_results['incorrect_predictions']
        if total_predictions > 0:
            accuracy = (test_results['correct_predictions'] / total_predictions) * 100
            print(f"Prediction accuracy: {accuracy:.1f}%")

        print(f"\nForbidden rate: {forbidden_rate:.1f}%")
        print(f"Authorized rate: {authorized_rate:.1f}%")

        print(f"\nExpected authorized commands:")
        print(f"  - update, file, slpf")
        print(f"  - query, features:*, slpf")
        print(f"  - allow, 130.0.16.0/20, slpf")
        print(f"All other commands should be FORBIDDEN (403)")


def test():
    logger.info("Creating Producer")
    oauth2_config = {  # keycloak config
        'client_id': 'Producer',
        'client_secret': 'RYuumxqGJwXTZP52Of5ImUcWEA4TnTUa',
        'redirect_uri': 'http://127.0.0.1:8000/callback',
        'callback_port': 8000
    }
    actuator_profile = slpf.Specifiers({
        'hostname': 'firewall',
        'named_group': 'firewalls',
        'asset_id': 'iptables'
    })
    args = slpf.Args({'response_requested': oc2.ResponseType.complete})

    try:
        oauth2authenticator = OAuth2Authenticator(**oauth2_config)
        p = oc2.Producer("producer.example.net", JSONEncoder(), HTTPTransfer("127.0.0.1", 9000),
                         authenticator=oauth2authenticator)

        cmd_list = load_json(command_path)
        print(f"Loaded {len(cmd_list)} commands for testing")

        for x in range(1, NUM_TESTS + 1):
            i=0
            for cmd_data in cmd_list:
                i+=1
                try:
                    cmd = oc2.Encoder.decode(oc2.Command, cmd_data)
                    command=oc2.Command(cmd.action, cmd.target, args, actuator=actuator_profile)
                    expected = classify_command_expectation(command)

                    logger.info("Sending command: %s", cmd)
                    resp = p.sendcmd(command)
                    logger.info("Got response: %s", resp)

                    check_response(cmd, resp, expected)

                    # Track prediction accuracy
                    if expected != 'unknown':
                        if ((resp.status == oc2.StatusCode.FORBIDDEN and expected == 'forbidden') or
                                ((resp.status == oc2.StatusCode.OK or resp.status == oc2.StatusCode.INTERNALERROR or resp.status == oc2.StatusCode.NOTIMPLEMENTED) and expected == 'allowed')):
                            test_results['correct_predictions'] += 1
                        else:
                            print(f"{command} {i}")
                            test_results['incorrect_predictions'] += 1

                except Exception as e:
                    test_results['errors'] += 1
                    logger.error(f"Error processing command {cmd_data}: {e}")
                    print(f"✗ ERROR processing command: {e}, {cmd_data}")

        print_test_summary()

    except Exception as e:
        logger.error(f"Failed to initialize test: {e}")
        print(f"Test initialization failed: {e}")


if __name__ == '__main__':
    test()