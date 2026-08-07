import React from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';

export default function LoginScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>AI Attendance System</Text>
      <Text style={styles.subtitle}>Login screen placeholder</Text>
      <Button title="Go to Dashboard" onPress={() => navigation.replace('Dashboard')} />
      <View style={styles.spacer} />
      <Button title="Create account" onPress={() => navigation.navigate('Register')} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    marginBottom: 24,
    color: '#555',
  },
  spacer: {
    height: 16,
  },
});