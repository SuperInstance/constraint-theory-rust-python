use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use flux_constraint::constraint::{ConstraintEngine, sat8};

fn bench_sat8(c: &mut Criterion) {
    let mut group = c.benchmark_group("sat8");
    for &val in &[0i32, 50, -50, 127, -127, 200, -200, i32::MAX, i32::MIN] {
        group.bench_with_input(BenchmarkId::new("value", val), &val, |b, &v| {
            b.iter(|| black_box(sat8(black_box(v))))
        });
    }
    group.finish();
}

fn bench_constraint_check(c: &mut Criterion) {
    let mut engine = ConstraintEngine::new();
    engine.add_constraint(0, 100, "speed", 2);
    engine.add_constraint(-40, 85, "temp", 3);
    engine.add_constraint(15, 55, "battery", 3);
    engine.add_constraint(0, 250, "rpm_scaled", 1);
    engine.add_constraint(-127, 127, "generic", 0);

    c.bench_function("check_single_5_constraints", |b| {
        b.iter(|| engine.check(black_box(50)))
    });
}

fn bench_batch(c: &mut Criterion) {
    let engine = ConstraintEngine::from_preset("battery").unwrap();
    let values: Vec<i32> = (0..10_000).map(|v| (v % 256) - 128).collect();

    let mut group = c.benchmark_group("batch");
    group.bench_function("sequential_10k", |b| {
        b.iter(|| engine.check_batch(black_box(&values)))
    });
    group.bench_function("parallel_10k", |b| {
        b.iter(|| engine.check_batch_parallel(black_box(&values)))
    });
    group.finish();
}

fn bench_presets(c: &mut Criterion) {
    let mut group = c.benchmark_group("presets");
    for name in &["battery", "automotive", "aviation", "nuclear", "marine", "medical"] {
        let engine = ConstraintEngine::from_preset(name).unwrap();
        group.bench_function(*name, |b| {
            b.iter(|| {
                for v in (-128..128).step_by(13) {
                    black_box(engine.check(black_box(v)));
                }
            })
        });
    }
    group.finish();
}

criterion_group!(benches, bench_sat8, bench_constraint_check, bench_batch, bench_presets);
criterion_main!(benches);
