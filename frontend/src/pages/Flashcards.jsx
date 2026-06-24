import React, { useEffect, useMemo, useState } from 'react';
import API from '../services/api';

const Flashcards = () => {
  const [cards, setCards] = useState([]);
  const [search, setSearch] = useState('');
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [flipped, setFlipped] = useState({});
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editDraft, setEditDraft] = useState({ question: '', answer: '' });

  const pageSize = 6;

  const loadCards = async () => {
    try {
      setLoading(true);
      const res = await API.get('/flashcards', { params: { search, favorite: favoriteOnly } });
      setCards(res.data || []);
      setPage(1);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCards();
  }, [favoriteOnly]);

  const filteredCards = useMemo(() => {
    const q = search.toLowerCase();
    return cards.filter((card) => {
      if (!q) return true;
      return `${card.question} ${card.answer}`.toLowerCase().includes(q);
    });
  }, [cards, search]);

  const pagedCards = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredCards.slice(start, start + pageSize);
  }, [filteredCards, page]);

  const totalPages = Math.max(1, Math.ceil(filteredCards.length / pageSize));

  const toggleFavorite = async (id) => {
    try {
      await API.post(`/flashcards/${id}/favorite`);
      loadCards();
    } catch (err) {
      console.error(err);
    }
  };

  const deleteCard = async (id) => {
    try {
      await API.delete(`/flashcards/${id}`);
      loadCards();
    } catch (err) {
      console.error(err);
    }
  };

  const startEdit = (card) => {
    setEditingId(card.id);
    setEditDraft({ question: card.question, answer: card.answer });
  };

  const saveEdit = async (id) => {
    try {
      await API.put(`/flashcards/${id}`, {
        question: editDraft.question,
        answer: editDraft.answer,
      });
      setEditingId(null);
      loadCards();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '100px auto 40px', padding: '0 20px' }}>
      <div className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div>
            <h1 style={{ fontSize: '1.9rem', marginBottom: '6px' }}>My Flashcards</h1>
            <p style={{ color: 'hsl(var(--text-secondary))', margin: 0 }}>Review, edit, favorite, and search your study cards.</p>
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search cards"
              style={{ padding: '10px 12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.15)', minWidth: '220px' }}
            />
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'hsl(var(--text-secondary))' }}>
              <input type="checkbox" checked={favoriteOnly} onChange={() => setFavoriteOnly(!favoriteOnly)} />
              Favorites only
            </label>
          </div>
        </div>

        {loading ? (
          <p style={{ marginTop: '20px' }}>Loading flashcards...</p>
        ) : filteredCards.length === 0 ? (
          <p style={{ marginTop: '20px' }}>No flashcards found yet. Generate some from upload.</p>
        ) : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginTop: '24px' }}>
              {pagedCards.map((card) => (
                <div key={card.id} className="glass-panel" style={{ padding: '16px', minHeight: '220px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'hsl(var(--primary))' }}>{card.difficulty}</span>
                    <button onClick={() => toggleFavorite(card.id)} style={{ border: 'none', background: 'transparent', cursor: 'pointer' }}>
                      {card.is_favorite ? '★' : '☆'}
                    </button>
                  </div>

                  {editingId === card.id ? (
                    <div>
                      <textarea
                        value={editDraft.question}
                        onChange={(e) => setEditDraft({ ...editDraft, question: e.target.value })}
                        style={{ width: '100%', marginBottom: '8px', minHeight: '70px' }}
                      />
                      <textarea
                        value={editDraft.answer}
                        onChange={(e) => setEditDraft({ ...editDraft, answer: e.target.value })}
                        style={{ width: '100%', marginBottom: '8px', minHeight: '70px' }}
                      />
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button onClick={() => saveEdit(card.id)} className="btn-primary">Save</button>
                        <button onClick={() => setEditingId(null)} className="btn-logout">Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div
                        onClick={() => setFlipped((prev) => ({ ...prev, [card.id]: !prev[card.id] }))}
                        style={{ cursor: 'pointer', minHeight: '120px' }}
                      >
                        <h3 style={{ fontSize: '1rem', marginBottom: '10px' }}>{flipped[card.id] ? 'Answer' : 'Question'}</h3>
                        <p style={{ color: 'hsl(var(--text-secondary))', lineHeight: 1.5 }}>
                          {flipped[card.id] ? card.answer : card.question}
                        </p>
                      </div>
                      <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                        <button onClick={() => startEdit(card)} className="btn-logout">Edit</button>
                        <button onClick={() => deleteCard(card.id)} className="btn-logout">Delete</button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '20px' }}>
              <button disabled={page === 1} onClick={() => setPage(page - 1)} className="btn-logout">Previous</button>
              <span>Page {page} / {totalPages}</span>
              <button disabled={page === totalPages} onClick={() => setPage(page + 1)} className="btn-logout">Next</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Flashcards;
