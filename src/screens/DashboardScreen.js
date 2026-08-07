import React from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';

export default function DashboardScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Dashboard</Text>
      <Text style={styles.subtitle}>Use the buttons below to continue.</Text>
      <View style={styles.buttonGroup}>
        <Button title="Attendance" onPress={() => navigation.navigate('Attendance')} />
      </View>
      <View style={styles.buttonGroup}>
        <Button title="Camera & Microphone" onPress={() => navigation.navigate('Permissions')} />
      </View>
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
    textAlign: 'center',
  },
  buttonGroup: {
    width: '100%',
    marginVertical: 8,
  },
});