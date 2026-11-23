"""对调用者已核实的事实应用优先级。规则含义和冲突事实由执行者判定。"""
import argparse
import json


def decide(*, dependency_change=False, dependency_approved=False, security_override=False,
           migration=False, compatible=True, material=False, prior_decision=False):
    if dependency_change and not dependency_approved:
        return "request-dependency-approval"
    if migration or not compatible:
        return "request-change-authorization" if not prior_decision else "apply-authorized-scope"
    if material and not (security_override or prior_decision):
        return "request-user-decision"
    if security_override:
        return "apply-version-matched-security-rule"
    return "apply-together-or-follow-existing-decision"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for flag in ("dependency-change", "dependency-approved", "security-override", "migration",
                 "material", "prior-decision"):
        parser.add_argument(f"--{flag}", action="store_true")
    parser.add_argument("--incompatible", action="store_false", dest="compatible")
    print(json.dumps({"decision": decide(**vars(parser.parse_args()))}))
