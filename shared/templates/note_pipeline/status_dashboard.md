# 状態ダッシュボード

「6ステップのどこで止まっているか」を一目で見る方法。

## ワンライナー（全記事の状態を一覧）

```bash
cd /home/ikuto/ai-company-os/shared/articles
for d in */; do
  [ "$d" = "_template/" ] && continue
  meta="$d/meta.yaml"
  [ -f "$meta" ] || continue
  python3 -c "
import yaml, sys
m = yaml.safe_load(open('$meta'))
slug = m.get('slug', '?')
target = m.get('target_publish_at', '?')
current = '?'
for step, info in m.get('pipeline', {}).items():
    s = info.get('status', '?')
    if s == 'in_progress':
        current = step + ' (in_progress, owner=' + info.get('owner','?') + ')'
        break
    elif s == 'blocked':
        current = step + ' (BLOCKED, owner=' + info.get('owner','?') + ')'
        break
    elif s == 'pending':
        current = step + ' (waiting, owner=' + info.get('owner','?') + ')'
        break
else:
    current = 'all done'
print(f'{slug:30s}  target={target}  → {current}')
"
done
```

## 出力例

```
2026-05-18-first-post           target=2026-05-18  → 1_generate (waiting, owner=hoshino_ritsu)
2026-05-22-second-post          target=2026-05-22  → 3_audit (BLOCKED, owner=kagura_aoi)
2026-05-25-third-post           target=2026-05-25  → all done
```

## 詰まっている記事だけ抽出

`BLOCKED` でgrepすれば、止まっているものだけ出る：

```bash
（上記コマンド） | grep BLOCKED
```

## 自分担当の記事だけ抽出

```bash
（上記コマンド） | grep "owner=shirase_kai"
```

## 将来：cronで毎朝Discord投稿

`🗓今日の業務` チャンネルに、毎朝このダッシュボードを自動投稿する。
誰が今日何を進めるべきかが一目で分かる。実装は次の出荷で。
