#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
# PR6 deploy — push utils.js v4 (nav: 3 new suites) + verify served assets.
# Static page files are already live via the shared workspace volume.
# Run after user approval: bash redesign-2026-09/deploy-pr6.sh
# ══════════════════════════════════════════════════════════════════════
set -e
V=root@147.93.113.241
BASE=/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data/agentic-os/dashboard

echo "── 1) push utils.js v4 (root-owned path)"
ssh -o BatchMode=yes $V "cat > $BASE/utils.js && chown root:root $BASE/utils.js && chmod 644 $BASE/utils.js && md5sum $BASE/utils.js" < /tmp/aos-utils-v4.js
echo "local md5:  $(md5sum /tmp/aos-utils-v4.js | cut -d' ' -f1)"

echo "── 2) verify served bundle"
curl -sk "https://os.srv1738752.hstgr.cloud/dashboard/utils.js" -o /tmp/served-utils4.js -w "utils.js HTTP %{http_code}\n"
echo "new pages in served utils: $(grep -c "compliance-suite\|grand-rounds-hub\|crm-suite" /tmp/served-utils4.js) matches"
curl -sk -o /dev/null -w "compliance-suite.js HTTP %{http_code}\n" "https://os.srv1738752.hstgr.cloud/dashboard/pages/compliance-suite.js"
curl -sk -o /dev/null -w "grand-rounds-hub.js HTTP %{http_code}\n" "https://os.srv1738752.hstgr.cloud/dashboard/pages/grand-rounds-hub.js"
curl -sk -o /dev/null -w "crm-suite.js HTTP %{http_code}\n" "https://os.srv1738752.hstgr.cloud/dashboard/pages/crm-suite.js"
curl -sk "https://os.srv1738752.hstgr.cloud/dashboard/" | grep -o "v=20260917" | head -1
echo "DONE"
