import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip as RechartsTooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { formatINR, formatDate, truncate } from '../utils/format';
import './Dashboard.css';

export default function Dashboard({ parsedData }) {
  if (!parsedData) return null;

  const { transactions, summary } = parsedData;
  const { net, total_credit, total_debit, category_breakdown } = summary;

  // Prepare data for Pie Chart
  const pieData = category_breakdown.filter(c => c.total > 0).map(c => ({
    name: c.category,
    value: c.total,
    color: c.color
  }));

  // Render tx history
  const renderTx = (tx) => {
    const isCredit = tx.type === 'credit';
    const amountStr = (isCredit ? '+' : '-') + formatINR(tx.amount);
    
    return (
      <div key={tx.id} className="tx-item glass-hover anim-fadeup" style={{animationDelay: `${parseInt(tx.id.replace('tx_', '')) * 50}ms`}}>
        <div className="tx-icon">
          {summary.categories_meta[tx.category]?.emoji || '💼'}
        </div>
        <div className="tx-details">
          <div className="tx-merchant">{truncate(tx.merchant, 25)}</div>
          <div className="tx-sub">
            {formatDate(tx.date)} • {tx.category}
          </div>
        </div>
        <div className={`tx-amount ${isCredit ? 'credit' : 'debit'}`}>
          {amountStr}
        </div>
      </div>
    );
  };

  return (
    <div className="dashboard-page anim-fadein">
      {/* Top Stats Cards */}
      <div className="stats-grid grid-3">
        <div className="stat-card glass">
          <div className="stat-label">Total Spent</div>
          <div className="stat-value text-red">{formatINR(total_debit)}</div>
        </div>
        <div className="stat-card glass">
          <div className="stat-label">Total Received</div>
          <div className="stat-value text-green">{formatINR(total_credit)}</div>
        </div>
        <div className="stat-card glass">
          <div className="stat-label">Net Flow</div>
          <div className={`stat-value ${net >= 0 ? 'text-green' : 'text-red'}`}>
            {net > 0 ? '+' : ''}{formatINR(net)}
          </div>
        </div>
      </div>

      <div className="dashboard-main grid-2">
        {/* Left Col: Charts */}
        <div className="charts-col flex-col gap-4">
          <div className="chart-card glass">
            <h3>Spending by Category</h3>
            {total_debit > 0 ? (
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip 
                      formatter={(value) => formatINR(value)}
                      contentStyle={{ background: 'rgba(10,14,26,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-state">No debit transactions found.</div>
            )}
          </div>

          <div className="category-list glass">
            <h3>Breakdown</h3>
            <div className="cat-items">
              {category_breakdown.map(cat => (
                <div key={cat.category} className="cat-row">
                  <div className="cat-left">
                    <span className="cat-icon">{cat.emoji}</span>
                    <span className="cat-name">{cat.category}</span>
                  </div>
                  <div className="cat-right">
                    <span className="cat-amt">{formatINR(cat.total)}</span>
                    <span className="cat-pct">{cat.percentage}%</span>
                  </div>
                  <div className="cat-bar-bg">
                    <div className="cat-bar-fill" style={{ width: `${cat.percentage}%`, background: cat.color }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Transactions */}
        <div className="tx-list-col">
          <div className="tx-list-card glass">
            <h3>Recent Transactions ({transactions.length})</h3>
            <div className="tx-list">
              {transactions.map(renderTx)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
