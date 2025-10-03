"""
Модуль интеграции биржевых данных с системой криптосуда.
Объединяет данные с BingX API для более точного анализа и формирования позиций.
"""

import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Безопасный импорт bingx_client
from utils.import_helper import get_bingx_client
from utils.logger import get_logger
bingx_client = get_bingx_client()

logger = get_logger(__name__)


class CryptoExchangeIntegration:
    """
    Класс для интеграции биржевых данных с системой криптосуда.
    Предоставляет расширенные данные для анализа и принятия решений.
    """
    
    def __init__(self):
        """Инициализация интеграции с биржей."""
        self.client = bingx_client
        self.cache = {}
        self.cache_ttl = 60  # Время жизни кэша в секундах
    
    def _get_cached_data(self, key: str) -> Optional[Dict]:
        """Получает данные из кэша."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def _set_cached_data(self, key: str, data: Dict):
        """Сохраняет данные в кэш."""
        self.cache[key] = (data, time.time())
    
    def get_comprehensive_market_data(self, symbol: str) -> Dict:
        """
        Получает комплексные рыночные данные для анализа.
        
        Args:
            symbol: Торговая пара
            
        Returns:
            Словарь с комплексными данными
        """
        cache_key = f"market_data_{symbol}"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached
        
        try:
            # Получаем различные типы данных
            ticker = self.client.get_ticker_24hr(symbol)
            order_book = self.client.get_order_book(symbol, limit=50)
            recent_trades = self.client.get_recent_trades(symbol, limit=100)
            klines_1h = self.client.get_klines(symbol, interval='1h', limit=24)
            klines_4h = self.client.get_klines(symbol, interval='4h', limit=30)
            
            # Анализируем настроения
            sentiment = self.client.analyze_market_sentiment(symbol, '1h')
            
            # Формируем комплексные данные
            comprehensive_data = {
                'symbol': symbol,
                'timestamp': int(time.time() * 1000),
                'ticker': ticker,
                'order_book': order_book,
                'recent_trades': recent_trades,
                'klines_1h': klines_1h,
                'klines_4h': klines_4h,
                'sentiment': sentiment,
                'analysis': self._analyze_market_structure(symbol, ticker, order_book, recent_trades)
            }
            
            self._set_cached_data(cache_key, comprehensive_data)
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive market data for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol}
    
    def _analyze_market_structure(self, symbol: str, ticker: Dict, 
                                 order_book: Dict, recent_trades: Dict) -> Dict:
        """
        Анализирует структуру рынка на основе полученных данных.
        
        Args:
            symbol: Торговая пара
            ticker: Данные тикера
            order_book: Стакан заявок
            recent_trades: Последние сделки
            
        Returns:
            Словарь с анализом структуры рынка
        """
        analysis = {
            'symbol': symbol,
            'liquidity_score': 0,
            'volatility_score': 0,
            'trend_strength': 0,
            'support_resistance': {},
            'volume_analysis': {},
            'order_flow': {}
        }
        
        try:
            # Анализ ликвидности
            if order_book and 'bids' in order_book and 'asks' in order_book:
                bid_depth = sum(float(bid[1]) for bid in order_book['bids'][:10])
                ask_depth = sum(float(ask[1]) for ask in order_book['asks'][:10])
                analysis['liquidity_score'] = min(bid_depth, ask_depth)
                analysis['order_flow'] = {
                    'bid_depth': bid_depth,
                    'ask_depth': ask_depth,
                    'imbalance': (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0
                }
            
            # Анализ волатильности
            if ticker:
                high = float(ticker.get('highPrice', 0))
                low = float(ticker.get('lowPrice', 0))
                current = float(ticker.get('lastPrice', 0))
                
                if current > 0:
                    volatility = ((high - low) / current) * 100
                    analysis['volatility_score'] = volatility
            
            # Анализ объема
            if ticker:
                volume = float(ticker.get('volume', 0))
                price_change = float(ticker.get('priceChangePercent', 0))
                
                analysis['volume_analysis'] = {
                    'volume_24h': volume,
                    'price_change_24h': price_change,
                    'volume_price_correlation': 'positive' if (volume > 0 and price_change > 0) else 'negative'
                }
            
            # Определение уровней поддержки и сопротивления
            if order_book and 'bids' in order_book and 'asks' in order_book:
                bids = [float(bid[0]) for bid in order_book['bids'][:5]]
                asks = [float(ask[0]) for ask in order_book['asks'][:5]]
                
                analysis['support_resistance'] = {
                    'nearest_support': max(bids) if bids else 0,
                    'nearest_resistance': min(asks) if asks else 0,
                    'support_levels': bids,
                    'resistance_levels': asks
                }
            
            # Анализ силы тренда
            if ticker:
                price_change = float(ticker.get('priceChangePercent', 0))
                if abs(price_change) > 5:
                    analysis['trend_strength'] = 'strong'
                elif abs(price_change) > 2:
                    analysis['trend_strength'] = 'moderate'
                else:
                    analysis['trend_strength'] = 'weak'
            
        except Exception as e:
            logger.error(f"Error analyzing market structure for {symbol}: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def get_crypto_sud_data(self, symbols: List[str] = None) -> Dict:
        """
        Получает данные для криптосуда по нескольким символам.
        
        Args:
            symbols: Список торговых пар для анализа
            
        Returns:
            Словарь с данными для криптосуда
        """
        if not symbols:
            symbols = ['BTC-USDT', 'ETH-USDT', 'BNB-USDT', 'ADA-USDT', 'SOL-USDT']
        
        sud_data = {
            'timestamp': int(time.time() * 1000),
            'symbols': {},
            'market_overview': {},
            'trending_pairs': [],
            'risk_assessment': {}
        }
        
        # Получаем данные по каждому символу
        for symbol in symbols:
            try:
                market_data = self.get_comprehensive_market_data(symbol)
                if 'error' not in market_data:
                    sud_data['symbols'][symbol] = market_data
                    
                    # Определяем трендовые пары
                    if market_data.get('sentiment', {}).get('sentiment') in ['bullish', 'bearish']:
                        sud_data['trending_pairs'].append({
                            'symbol': symbol,
                            'sentiment': market_data['sentiment']['sentiment'],
                            'price_change': market_data['sentiment'].get('price_change_24h', 0)
                        })
                        
            except Exception as e:
                logger.error(f"Error getting data for {symbol}: {e}")
        
        # Сортируем трендовые пары по изменению цены
        sud_data['trending_pairs'].sort(key=lambda x: abs(x['price_change']), reverse=True)
        
        # Общая оценка риска
        sud_data['risk_assessment'] = self._assess_market_risk(sud_data['symbols'])
        
        return sud_data
    
    def _assess_market_risk(self, symbols_data: Dict) -> Dict:
        """
        Оценивает общий риск рынка на основе данных по символам.
        
        Args:
            symbols_data: Данные по символам
            
        Returns:
            Словарь с оценкой риска
        """
        risk_assessment = {
            'overall_risk': 'low',
            'volatility_level': 'low',
            'liquidity_concerns': False,
            'trend_consistency': 'neutral',
            'risk_factors': []
        }
        
        try:
            total_volatility = 0
            total_liquidity = 0
            bullish_count = 0
            bearish_count = 0
            symbol_count = len(symbols_data)
            
            for symbol, data in symbols_data.items():
                # Собираем статистику
                sentiment = data.get('sentiment', {})
                analysis = data.get('analysis', {})
                
                total_volatility += analysis.get('volatility_score', 0)
                total_liquidity += analysis.get('liquidity_score', 0)
                
                if sentiment.get('sentiment') == 'bullish':
                    bullish_count += 1
                elif sentiment.get('sentiment') == 'bearish':
                    bearish_count += 1
            
            # Оценка волатильности
            avg_volatility = total_volatility / symbol_count if symbol_count > 0 else 0
            if avg_volatility > 10:
                risk_assessment['volatility_level'] = 'high'
                risk_assessment['risk_factors'].append('high_volatility')
            elif avg_volatility > 5:
                risk_assessment['volatility_level'] = 'medium'
            
            # Оценка ликвидности
            avg_liquidity = total_liquidity / symbol_count if symbol_count > 0 else 0
            if avg_liquidity < 1000:  # Пороговое значение
                risk_assessment['liquidity_concerns'] = True
                risk_assessment['risk_factors'].append('low_liquidity')
            
            # Оценка консистентности тренда
            if bullish_count > bearish_count * 2:
                risk_assessment['trend_consistency'] = 'bullish'
            elif bearish_count > bullish_count * 2:
                risk_assessment['trend_consistency'] = 'bearish'
            
            # Общая оценка риска
            risk_factors_count = len(risk_assessment['risk_factors'])
            if risk_factors_count >= 2 or avg_volatility > 15:
                risk_assessment['overall_risk'] = 'high'
            elif risk_factors_count >= 1 or avg_volatility > 8:
                risk_assessment['overall_risk'] = 'medium'
            
        except Exception as e:
            logger.error(f"Error assessing market risk: {e}")
            risk_assessment['error'] = str(e)
        
        return risk_assessment
    
    def get_position_recommendations(self, symbol: str, user_balance: float = None) -> Dict:
        """
        Генерирует рекомендации по позициям на основе анализа данных.
        
        Args:
            symbol: Торговая пара
            user_balance: Баланс пользователя (опционально)
            
        Returns:
            Словарь с рекомендациями
        """
        try:
            market_data = self.get_comprehensive_market_data(symbol)
            
            if 'error' in market_data:
                return {'error': market_data['error']}
            
            sentiment = market_data.get('sentiment', {})
            analysis = market_data.get('analysis', {})
            ticker = market_data.get('ticker', {})
            
            recommendation = {
                'symbol': symbol,
                'action': 'hold',
                'confidence': 0.5,
                'reasoning': [],
                'risk_level': 'medium',
                'position_size': 0,
                'stop_loss': 0,
                'take_profit': 0
            }
            
            # Анализ настроений
            if sentiment.get('sentiment') == 'bullish':
                recommendation['action'] = 'buy'
                recommendation['confidence'] += 0.2
                recommendation['reasoning'].append('Положительные настроения рынка')
            elif sentiment.get('sentiment') == 'bearish':
                recommendation['action'] = 'sell'
                recommendation['confidence'] += 0.2
                recommendation['reasoning'].append('Отрицательные настроения рынка')
            
            # Анализ тренда
            if analysis.get('trend_strength') == 'strong':
                recommendation['confidence'] += 0.15
                recommendation['reasoning'].append('Сильный тренд')
            elif analysis.get('trend_strength') == 'weak':
                recommendation['confidence'] -= 0.1
                recommendation['reasoning'].append('Слабый тренд')
            
            # Анализ ликвидности
            liquidity_score = analysis.get('liquidity_score', 0)
            if liquidity_score > 10000:
                recommendation['confidence'] += 0.1
                recommendation['reasoning'].append('Высокая ликвидность')
            elif liquidity_score < 1000:
                recommendation['confidence'] -= 0.15
                recommendation['reasoning'].append('Низкая ликвидность')
            
            # Расчет размера позиции
            if user_balance and user_balance > 0:
                current_price = float(ticker.get('lastPrice', 0))
                if current_price > 0:
                    # Рекомендуем использовать 5-15% баланса в зависимости от уверенности
                    position_percentage = min(0.15, max(0.05, recommendation['confidence']))
                    recommendation['position_size'] = user_balance * position_percentage
                    
                    # Расчет стоп-лосса и тейк-профита
                    if recommendation['action'] == 'buy':
                        recommendation['stop_loss'] = current_price * 0.95  # -5%
                        recommendation['take_profit'] = current_price * 1.15  # +15%
                    elif recommendation['action'] == 'sell':
                        recommendation['stop_loss'] = current_price * 1.05  # +5%
                        recommendation['take_profit'] = current_price * 0.85  # -15%
            
            # Оценка риска
            volatility = analysis.get('volatility_score', 0)
            if volatility > 15:
                recommendation['risk_level'] = 'high'
            elif volatility < 5:
                recommendation['risk_level'] = 'low'
            
            # Ограничиваем уверенность
            recommendation['confidence'] = max(0.1, min(0.95, recommendation['confidence']))
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating position recommendations for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol}


# Создаем глобальный экземпляр интеграции
crypto_integration = CryptoExchangeIntegration() 