//! Package-fill component lifecycle through the full backtest engine: a
//! marketable limit order on a generic spread fills as one package whose
//! correlated component fills book the leg positions, and the ordinary option
//! settlement at expiration closes them. The spread itself never opens a
//! position, and an opposite package execution unwinds the component exposure
//! before expiry.

use std::cell::RefCell;
use std::rc::Rc;

use nautilus_backtest::{
    config::{BacktestEngineConfig, SimulatedVenueConfig},
    engine::BacktestEngine,
};
use nautilus_execution::models::fee::{FeeModelAny, MakerTakerFeeModel};
use nautilus_model::{
    data::{Data, IndexPriceUpdate, QuoteTick},
    enums::{AccountType, AssetClass, BookType, OmsType, OptionKind, OrderSide, PositionSide},
    events::OrderFilled,
    identifiers::{InstrumentId, Symbol, Venue, new_generic_spread_id},
    instruments::{IndexInstrument, InstrumentAny, OptionContract, OptionSpread},
    types::{Currency, Money, Price, Quantity},
};
use nautilus_trading::{
    nautilus_strategy,
    strategy::{Strategy, StrategyConfig, StrategyCore},
};
use ustr::Ustr;

const VENUE_NAME: &str = "SPXW";
const EXPIRATION_NS: u64 = 100;

fn leg_contract(strike: u32, kind: OptionKind) -> OptionContract {
    let suffix = match kind {
        OptionKind::Call => "C",
        OptionKind::Put => "P",
    };
    OptionContract::builder()
        .instrument_id(InstrumentId::from(
            format!("SPXW{strike}{suffix}.{VENUE_NAME}").as_str(),
        ))
        .raw_symbol(Symbol::from(format!("SPXW{strike}{suffix}").as_str()))
        .asset_class(AssetClass::Index)
        .exchange(Ustr::from(VENUE_NAME))
        .underlying(Ustr::from("SPX"))
        .option_kind(kind)
        .strike_price(Price::from(strike.to_string().as_str()))
        .currency(Currency::USD())
        .activation_ns(nautilus_core::UnixNanos::default())
        .expiration_ns(nautilus_core::UnixNanos::from(EXPIRATION_NS))
        .price_precision(2)
        .price_increment(Price::from("0.05"))
        .multiplier(Quantity::from(1))
        .lot_size(Quantity::from(1))
        .ts_event(nautilus_core::UnixNanos::default())
        .ts_init(nautilus_core::UnixNanos::default())
        .build()
        .expect("leg instrument is valid")
}

fn spread_instrument(call: &OptionContract, put: &OptionContract) -> OptionSpread {
    let legs = vec![(call.id, 1), (put.id, -1)];
    let instrument_id = new_generic_spread_id(&legs).expect("test legs form a valid spread ID");
    let symbol = instrument_id.symbol.as_str().to_string();
    OptionSpread::builder()
        .instrument_id(instrument_id)
        .raw_symbol(Symbol::from(symbol.as_str()))
        .asset_class(AssetClass::Index)
        .exchange(Ustr::from(VENUE_NAME))
        .underlying(Ustr::from("SPX"))
        .strategy_type(Ustr::from("IC"))
        .activation_ns(nautilus_core::UnixNanos::default())
        .expiration_ns(nautilus_core::UnixNanos::from(EXPIRATION_NS))
        .currency(Currency::USD())
        .price_precision(2)
        .price_increment(Price::from("0.05"))
        .multiplier(Quantity::from(1))
        .lot_size(Quantity::from(1))
        .ts_event(nautilus_core::UnixNanos::default())
        .ts_init(nautilus_core::UnixNanos::default())
        .build()
        .expect("spread instrument is valid")
}

fn underlying_instrument() -> IndexInstrument {
    IndexInstrument::builder()
        .instrument_id(InstrumentId::from(format!("SPX.{VENUE_NAME}")))
        .raw_symbol(Symbol::from("SPX"))
        .currency(Currency::USD())
        .price_precision(2)
        .size_precision(0)
        .price_increment(Price::from("0.01"))
        .size_increment(Quantity::from(1))
        .ts_event(nautilus_core::UnixNanos::default())
        .ts_init(nautilus_core::UnixNanos::default())
        .build()
        .expect("underlying instrument is valid")
}

fn leg_quote(instrument_id: InstrumentId, bid: &str, ask: &str, ts: u64) -> Data {
    Data::Quote(QuoteTick::new(
        instrument_id,
        Price::from(bid),
        Price::from(ask),
        Quantity::from(10),
        Quantity::from(10),
        ts.into(),
        ts.into(),
    ))
}

fn venue_config() -> SimulatedVenueConfig {
    SimulatedVenueConfig::builder()
        .venue(Venue::from(VENUE_NAME))
        .oms_type(OmsType::Netting)
        .account_type(AccountType::Margin)
        .book_type(BookType::L1_MBP)
        .starting_balances(vec![Money::from("1_000_000 USD")])
        .fee_model(FeeModelAny::MakerTaker(MakerTakerFeeModel::zero()).into())
        .build()
        .expect("venue config is valid")
}

/// A fill observed by the strategy, recorded for component-accounting
/// assertions.
#[derive(Debug)]
struct ObservedFill {
    instrument_id: InstrumentId,
    side: OrderSide,
    qty: Quantity,
    px: Price,
}

struct ComboProbe {
    core: StrategyCore,
    spread_id: InstrumentId,
    entry_submitted: bool,
    unwind_submitted: bool,
    fills: Rc<RefCell<Vec<ObservedFill>>>,
}

impl ComboProbe {
    fn new(spread_id: InstrumentId) -> Self {
        Self {
            core: StrategyCore::new(StrategyConfig::default()),
            spread_id,
            entry_submitted: false,
            unwind_submitted: false,
            fills: Rc::new(RefCell::new(Vec::new())),
        }
    }
}

nautilus_strategy!(ComboProbe, {
    fn on_order_filled(&mut self, event: &OrderFilled) {
        self.fills.borrow_mut().push(ObservedFill {
            instrument_id: event.instrument_id,
            side: event.order_side,
            qty: event.last_qty,
            px: event.last_px,
        });
    }
});

impl std::fmt::Debug for ComboProbe {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ComboProbe")
            .field("spread_id", &self.spread_id)
            .field("entry_submitted", &self.entry_submitted)
            .field("unwind_submitted", &self.unwind_submitted)
            .finish_non_exhaustive()
    }
}

impl nautilus_common::actor::data_actor::DataActor for ComboProbe {
    fn on_start(&mut self) -> anyhow::Result<()> {
        self.subscribe_quotes(self.spread_id, None, None);
        Ok(())
    }

    fn on_quote(&mut self, quote: &QuoteTick) -> anyhow::Result<()> {
        if quote.instrument_id != self.spread_id {
            return Ok(());
        }

        // The first spread quote triggers the entry sell at the leg-derived
        // net bid; a second quote triggers the opposite buy that unwinds the
        // component exposure before expiration.
        let (side, limit_price) = if !self.entry_submitted {
            self.entry_submitted = true;
            (OrderSide::Sell, "0.80")
        } else if !self.unwind_submitted {
            self.unwind_submitted = true;
            (OrderSide::Buy, "1.25")
        } else {
            return Ok(());
        };

        let order = self.order().limit(
            self.spread_id,
            side,
            Quantity::from(1),
            Price::from(limit_price),
            None, // time_in_force
            None, // expire_time
            None, // post_only
            None, // reduce_only
            None, // quote_quantity
            None, // display_qty
            None, // emulation_trigger
            None, // trigger_instrument_id
            None, // exec_algorithm_id
            None, // exec_algorithm_params
            None, // tags
            None, // client_order_id
        );
        self.submit_order(order, None, None, None)
    }
}

/// Asserts the leading observed fills match `(instrument, side, price)`
/// exactly; settlement fills may follow the entry sequence.
fn assert_fill_prefix(observed: &[ObservedFill], expected: &[(InstrumentId, OrderSide, &str)]) {
    assert!(
        observed.len() >= expected.len(),
        "expected at least {} fills, got {observed:?}",
        expected.len()
    );
    for (fill, (instrument_id, side, px)) in observed.iter().zip(expected) {
        assert_eq!(
            fill.instrument_id, *instrument_id,
            "unexpected fill sequence {observed:?}"
        );
        assert_eq!(fill.side, *side);
        assert_eq!(fill.qty, Quantity::from(1));
        assert_eq!(fill.px, Price::from(px));
    }
}

#[test]
fn test_package_fill_books_component_positions_that_option_settlement_closes() {
    let call = leg_contract(6000, OptionKind::Call);
    let put = leg_contract(6000, OptionKind::Put);
    let spread = spread_instrument(&call, &put);
    let spread_id = spread.id;

    let mut engine = BacktestEngine::new(BacktestEngineConfig {
        bypass_logging: true,
        run_analysis: false,
        ..Default::default()
    })
    .expect("engine initializes");
    engine.add_venue(venue_config()).expect("venue is added");
    engine
        .add_instrument(&InstrumentAny::IndexInstrument(underlying_instrument()))
        .expect("underlying instrument is added");
    engine
        .add_instrument(&InstrumentAny::OptionContract(call.clone()))
        .expect("call instrument is added");
    engine
        .add_instrument(&InstrumentAny::OptionContract(put.clone()))
        .expect("put instrument is added");
    engine
        .add_instrument(&InstrumentAny::OptionSpread(spread))
        .expect("spread instrument is added");
    let probe = ComboProbe::new(spread_id);
    let fills = Rc::clone(&probe.fills);
    engine.add_strategy(probe).expect("strategy is added");

    let data = vec![
        leg_quote(call.id, "10.90", "11.10", 1),
        leg_quote(put.id, "9.90", "10.10", 1),
        // The index level at expiration fixes the cash-settled intrinsic
        // value of each leg (both legs expire worthless at spot 6000)
        Data::IndexPrice(IndexPriceUpdate::new(
            InstrumentId::from(format!("SPX.{VENUE_NAME}")),
            Price::from("6000.00"),
            1.into(),
            1.into(),
        )),
        // The spread quote triggers the strategy's marketable sell limit
        // order, which fills as one package at the leg-derived net price
        leg_quote(spread_id, "0.80", "1.20", 2),
        // Post-expiration quotes advance each engine past expiration so the
        // component legs settle through their own option paths and the
        // spread reconciles its component accounting
        leg_quote(call.id, "10.90", "11.10", EXPIRATION_NS + 1),
        leg_quote(put.id, "9.90", "10.10", EXPIRATION_NS + 1),
        leg_quote(spread_id, "0.80", "1.20", EXPIRATION_NS + 1),
    ];
    engine
        .add_data(data, None, true, true)
        .expect("data is added");
    engine.run(None, None, None, false).expect("run completes");

    // The correlated component fills dispatch before the package fill
    // reports: the call sells at its bid, the put buys at its ask, and the
    // package reports the derived net credit.
    assert_fill_prefix(
        &fills.borrow(),
        &[
            (call.id, OrderSide::Sell, "10.90"),
            (put.id, OrderSide::Buy, "10.10"),
            (spread_id, OrderSide::Sell, "0.80"),
        ],
    );

    let cache = engine.kernel().cache.clone();
    let cache = cache.borrow();
    assert_eq!(
        cache.positions_open_count(None, None, None, None, None),
        0,
        "the component legs must settle to closed positions"
    );
    assert!(
        cache
            .positions_closed(None, Some(&spread_id), None, None, None)
            .is_empty(),
        "the package fill must never open a spread position"
    );

    let call_positions = cache.positions_closed(None, Some(&call.id), None, None, None);
    assert_eq!(call_positions.len(), 1, "one closed call position");
    let call_position = &call_positions[0];
    assert_eq!(call_position.side, PositionSide::Flat);
    assert_eq!(call_position.peak_qty, Quantity::from(1));
    assert_eq!(
        call_position.entry,
        OrderSide::Sell,
        "the component sell opens the short call"
    );
    assert!(
        (call_position.avg_px_open - 10.90).abs() < 1e-9,
        "component fill at the actual leg bid, got {}",
        call_position.avg_px_open
    );
    assert_eq!(
        call_position.realized_pnl,
        Some(Money::new(10.90, Currency::USD())),
        "the short call settles worthless at spot 6000"
    );

    let put_positions = cache.positions_closed(None, Some(&put.id), None, None, None);
    assert_eq!(put_positions.len(), 1, "one closed put position");
    let put_position = &put_positions[0];
    assert_eq!(put_position.side, PositionSide::Flat);
    assert_eq!(put_position.peak_qty, Quantity::from(1));
    assert_eq!(
        put_position.entry,
        OrderSide::Buy,
        "the component buy opens the long put"
    );
    assert!(
        (put_position.avg_px_open - 10.10).abs() < 1e-9,
        "component fill at the actual leg ask, got {}",
        put_position.avg_px_open
    );
    assert_eq!(
        put_position.realized_pnl,
        Some(Money::new(-10.10, Currency::USD())),
        "the long put settles worthless at spot 6000"
    );
}

#[test]
fn test_opposite_package_execution_unwinds_component_exposure_before_expiry() {
    let call = leg_contract(6000, OptionKind::Call);
    let put = leg_contract(6000, OptionKind::Put);
    let spread = spread_instrument(&call, &put);
    let spread_id = spread.id;

    let mut engine = BacktestEngine::new(BacktestEngineConfig {
        bypass_logging: true,
        run_analysis: false,
        ..Default::default()
    })
    .expect("engine initializes");
    engine.add_venue(venue_config()).expect("venue is added");
    engine
        .add_instrument(&InstrumentAny::IndexInstrument(underlying_instrument()))
        .expect("underlying instrument is added");
    engine
        .add_instrument(&InstrumentAny::OptionContract(call.clone()))
        .expect("call instrument is added");
    engine
        .add_instrument(&InstrumentAny::OptionContract(put.clone()))
        .expect("put instrument is added");
    engine
        .add_instrument(&InstrumentAny::OptionSpread(spread))
        .expect("spread instrument is added");
    let probe = ComboProbe::new(spread_id);
    let fills = Rc::clone(&probe.fills);
    engine.add_strategy(probe).expect("strategy is added");

    let data = vec![
        leg_quote(call.id, "10.90", "11.10", 1),
        leg_quote(put.id, "9.90", "10.10", 1),
        Data::IndexPrice(IndexPriceUpdate::new(
            InstrumentId::from(format!("SPX.{VENUE_NAME}")),
            Price::from("6000.00"),
            1.into(),
            1.into(),
        )),
        // The first spread quote triggers the entry sell; the second triggers
        // the opposite buy that unwinds the exposure before expiry
        leg_quote(spread_id, "0.80", "1.20", 2),
        leg_quote(spread_id, "0.80", "1.20", 3),
        // Post-expiration quotes advance each engine past expiration so the
        // spread reconciles its component accounting with nothing left to
        // settle
        leg_quote(call.id, "10.90", "11.10", EXPIRATION_NS + 1),
        leg_quote(put.id, "9.90", "10.10", EXPIRATION_NS + 1),
        leg_quote(spread_id, "0.80", "1.20", EXPIRATION_NS + 1),
    ];
    engine
        .add_data(data, None, true, true)
        .expect("data is added");
    engine.run(None, None, None, false).expect("run completes");

    // Each package fills as one correlated set: the entry credit books the
    // component positions, the opposite execution closes them at the actual
    // leg prices, and the package reports the derived net price.
    assert_fill_prefix(
        &fills.borrow(),
        &[
            (call.id, OrderSide::Sell, "10.90"),
            (put.id, OrderSide::Buy, "10.10"),
            (spread_id, OrderSide::Sell, "0.80"),
            (call.id, OrderSide::Buy, "11.10"),
            (put.id, OrderSide::Sell, "9.90"),
            (spread_id, OrderSide::Buy, "1.20"),
        ],
    );

    let cache = engine.kernel().cache.clone();
    let cache = cache.borrow();
    assert_eq!(
        cache.positions_open_count(None, None, None, None, None),
        0,
        "the opposite package execution must unwind the component exposure"
    );
    assert!(
        cache
            .positions_closed(None, Some(&spread_id), None, None, None)
            .is_empty(),
        "neither package execution may open a spread position"
    );

    let call_positions = cache.positions_closed(None, Some(&call.id), None, None, None);
    assert_eq!(call_positions.len(), 1, "one closed call position");
    let call_position = &call_positions[0];
    assert_eq!(call_position.side, PositionSide::Flat);
    assert_eq!(
        call_position.entry,
        OrderSide::Sell,
        "opened by the entry component sell"
    );
    assert!(
        (call_position.avg_px_open - 10.90).abs() < 1e-9,
        "got {}",
        call_position.avg_px_open
    );
    assert_eq!(
        call_position.realized_pnl,
        Some(Money::new(-0.20, Currency::USD())),
        "the short call unwinds at the ask"
    );

    let put_positions = cache.positions_closed(None, Some(&put.id), None, None, None);
    assert_eq!(put_positions.len(), 1, "one closed put position");
    let put_position = &put_positions[0];
    assert_eq!(put_position.side, PositionSide::Flat);
    assert_eq!(
        put_position.entry,
        OrderSide::Buy,
        "opened by the entry component buy"
    );
    assert!(
        (put_position.avg_px_open - 10.10).abs() < 1e-9,
        "got {}",
        put_position.avg_px_open
    );
    assert_eq!(
        put_position.realized_pnl,
        Some(Money::new(-0.20, Currency::USD())),
        "the long put unwinds at the bid"
    );
}
