import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FirewallRule:
    rule_id: int
    source: str
    destination: str
    port: str
    action: str


def load_rules(file_path: str) -> list[FirewallRule]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Файл не знайдено: {file_path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    rules = []

    for item in data:
        rule = FirewallRule(
            rule_id=int(item["id"]),
            source=item["source"],
            destination=item["destination"],
            port=str(item["port"]),
            action=item["action"].upper(),
        )
        rules.append(rule)

    return rules


def is_valid_ip_or_subnet(value: str) -> bool:
    if value.upper() == "ANY":
        return True

    pattern = (
        r"^(?:"
        r"(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
        r"(?:/(?:[0-9]|[12][0-9]|3[0-2]))?"
        r"$"
    )

    return re.fullmatch(pattern, value) is not None


def validate_rule(rule: FirewallRule) -> bool:
    source_valid = is_valid_ip_or_subnet(rule.source)
    destination_valid = is_valid_ip_or_subnet(rule.destination)

    return source_valid and destination_valid


def find_duplicates_and_conflicts(
    rules: list[FirewallRule],
) -> tuple[
    list[tuple[FirewallRule, FirewallRule]],
    list[tuple[FirewallRule, FirewallRule]],
]:
    grouped_rules = defaultdict(list)

    for rule in rules:
        key = (
            rule.source.upper(),
            rule.destination.upper(),
            rule.port.upper(),
        )
        grouped_rules[key].append(rule)

    duplicates = []
    conflicts = []

    for group in grouped_rules.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                first = group[i]
                second = group[j]

                if first.action == second.action:
                    duplicates.append((first, second))
                else:
                    conflicts.append((first, second))

    return duplicates, conflicts


def find_high_risk_rules(
    rules: list[FirewallRule],
) -> list[FirewallRule]:
    high_risk = []

    for rule in rules:
        if rule.action != "ALLOW":
            continue

        if rule.port.upper() == "ANY" or rule.source == "0.0.0.0/0":
            high_risk.append(rule)

    return high_risk


def save_rules_to_json(
    rules: list[FirewallRule],
    output_path: str,
) -> None:
    data = []

    for rule in rules:
        data.append(
            {
                "id": rule.rule_id,
                "source": rule.source,
                "destination": rule.destination,
                "port": rule.port,
                "action": rule.action,
            }
        )

    path = Path(output_path)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def setup_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
    )


def print_report(
    invalid_rules: list[FirewallRule],
    duplicates: list[tuple[FirewallRule, FirewallRule]],
    conflicts: list[tuple[FirewallRule, FirewallRule]],
    high_risk: list[FirewallRule],
) -> None:
    print("\n=== Firewall Configuration Audit Report ===")
    print(f"Invalid IP Formats : {len(invalid_rules)}")
    print(f"Conflicting Rules  : {len(conflicts)} conflicts found")
    print(f"Duplicate Rules    : {len(duplicates)} duplicates found")
    print(f"High-Risk Rules    : {len(high_risk)} dangerous ALLOW rules")

    print("\n=== Critical Findings ===")

    for first, second in conflicts:
        print(
            f"[CONFLICT] Rule #{first.rule_id} "
            f"({first.action} {first.source} -> "
            f"{first.destination}:{first.port}) "
            f"conflicts with Rule #{second.rule_id} "
            f"({second.action} {second.source} -> "
            f"{second.destination}:{second.port})"
        )

    for rule in high_risk:
        print(
            f"[HIGH-RISK] Rule #{rule.rule_id}: "
            f"{rule.action} {rule.source} -> "
            f"{rule.destination}:{rule.port}"
        )


def analyze_rules(
    rules_file: str,
    output: str,
    check_conflicts: bool,
    log_level: str,
) -> None:
    setup_logging(log_level)

    logger.info("Parsing firewall rules from %s...", rules_file)

    rules = load_rules(rules_file)

    logger.info(
        "Total rules parsed: %s. Validating IP syntax and rule logic...",
        len(rules),
    )

    valid_rules = []
    invalid_rules = []

    for rule in rules:
        if validate_rule(rule):
            valid_rules.append(rule)
        else:
            invalid_rules.append(rule)

    duplicates = []
    conflicts = []

    if check_conflicts:
        duplicates, conflicts = find_duplicates_and_conflicts(valid_rules)

    high_risk = find_high_risk_rules(valid_rules)

    print_report(
        invalid_rules,
        duplicates,
        conflicts,
        high_risk,
    )

    save_rules_to_json(valid_rules, output)

    logger.info(
        "Security report successfully exported to %s",
        output,
    )
