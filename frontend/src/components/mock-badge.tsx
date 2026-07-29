// 這個系統的產出會影響真實投資決策，所以「示範資料絕對不能看起來像真的」是硬性規則
// （見 PROJECT.md「真實 vs mock 資料對照」）。畫面上每一處還沒接真實來源的數字，
// 都要掛這個標記，讓使用者一眼看得出不能拿來做決策。
//
// 用法：
//   <MockBadge />                     行內小標籤，放在數字或標題旁
//   <MockBadge reason="等 FinMind" /> 滑鼠移上去會說明在等什麼資料源
//   <MockNotice />                    整區/整頁都是示範資料時，放在最上面的橫幅

export function MockBadge({ reason, className = "" }: { reason?: string; className?: string }) {
  return (
    <span
      title={reason ? `示範資料：${reason}` : "示範資料，非真實數據"}
      className={`inline-block shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium leading-none align-middle bg-amber-500/15 text-amber-400 border border-amber-500/30 ${className}`}
    >
      示範資料
    </span>
  )
}

export function MockNotice({ reason }: { reason?: string }) {
  return (
    <div className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
      <span aria-hidden="true">⚠</span>
      <p>
        這一區是<strong className="font-semibold">示範資料</strong>，不是真實市場數據，請勿用來做投資判斷。
        {reason && <span className="text-amber-400/80">（{reason}）</span>}
      </p>
    </div>
  )
}
