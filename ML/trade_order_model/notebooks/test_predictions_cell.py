# Test Set Predictions with Table Output
# Add this cell after model training

# Make predictions on test set
y_pred = model.predict(X_test)

# Create results dataframe
results_df = pd.DataFrame({
    'Actual': y_test,
    'Predicted': y_pred,
    'Difference': y_test - y_pred
})

# Display results in table format
print("\n📊 TEST SET PREDICTIONS")
print("="*60)
print(f"\nTotal Test Samples: {len(results_df)}")
print(f"Mean Absolute Error: {np.abs(results_df['Difference']).mean():.4f}")
print(f"Root Mean Squared Error: {np.sqrt((results_df['Difference']**2).mean()):.4f}")
print(f"R² Score: {r2_score(y_test, y_pred):.4f}")

print("\n📋 Sample Predictions (First 20 rows):")
print("-"*60)
display(results_df.head(20).style.format({
    'Actual': '{:.2f}',
    'Predicted': '{:.2f}',
    'Difference': '{:.2f}'
}))

# Save full results to CSV
results_df.to_csv('../outputs/test_predictions.csv', index=False)
print(f"\n✅ Full predictions saved to: ../outputs/test_predictions.csv")
