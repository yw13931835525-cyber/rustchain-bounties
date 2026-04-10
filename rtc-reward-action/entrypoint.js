const https = require('https');

async function httpPost(url, body) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const opts = {
      hostname: u.host, path: u.pathname, method: 'POST',
      headers: {'Content-Type': 'application/json'}
    };
    const req = https.request(opts, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve(d));
    });
    req.on('error', reject);
    req.write(JSON.stringify(body));
    req.end();
  });
}

async function main() {
  const event = require(process.env.GITHUB_EVENT_PATH);
  const core = require('@actions/core');
  const exec = require('@actions/exec');

  const nodeUrl = core.getInput('node-url') || 'https://50.28.86.131';
  const amount = core.getInput('amount') || '5';
  const walletFrom = core.getInput('wallet-from');
  const dryRun = core.getInput('dry-run') === 'true';
  const pr = event.pull_request;
  const prBody = pr.body || '';
  const author = pr.user.login;

  console.log(`=== RTC PR Reward ===`);
  console.log(`PR #${pr.number} by @${author}`);
  console.log(`Amount: ${amount} RTC`);

  // Extract wallet from PR body
  const match = prBody.match(/(?:rtc.?wallet|wallet|my.?wallet)[:\s]+([A-Za-z0-9_-]{5,})/i);
  const wallet = match ? match[1] : null;

  if (!wallet) {
    console.log('No wallet found in PR body — posting comment');
    const comment = `⚠️ **RTC Reward Pending** — No wallet found in PR body.

@${author} please add your RTC wallet to the PR description:
\`\`\`
wallet: YOUR_RTC_WALLET_NAME
\`\`\``;
    await exec.exec(`gh pr comment ${pr.number} --body "${comment.replace(/"/g, '\\"')}"`);
    return;
  }

  console.log(`Contributor wallet: ${wallet}`);
  let txResult = null;

  if (!dryRun) {
    try {
      const resp = await httpPost(`${nodeUrl}/api/send`, {
        from: walletFrom, to: wallet, amount: parseFloat(amount)
      });
      console.log('Payment response:', resp);
      txResult = JSON.parse(resp);
    } catch(e) {
      console.log('Payment error:', e.message);
    }
  } else {
    console.log('DRY RUN — no transaction sent');
  }

  const status = dryRun ? 'DRY RUN' : (txResult ? 'Sent' : 'Error');
  const comment = `✅ **RTC Reward ${status}!** — @${author} | **${amount} RTC** → \`${wallet}\`

| Field | Value |
|-------|-------|
| Amount | ${amount} RTC |
| Recipient | \`${wallet}\` |
| From wallet | \`${walletFrom}\` |
| PR | #${pr.number} |

*Powered by [rtc-reward-action](https://github.com/Scottcjn/rtc-reward-action)*`;

  await exec.exec(`gh pr comment ${pr.number} --body "${comment.replace(/"/g, '\\"')}"`);
}

main().catch(e => { console.error(e); process.exit(1); });
