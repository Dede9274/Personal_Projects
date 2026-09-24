import React from 'react';
import {StyleSheet, Text, useWindowDimensions, View} from 'react-native';
import CalendarPicker from 'react-native-calendar-picker';
import moment from 'moment';

const Calendar = ({value, onDateChange, minDate}) => {
  const {width} = useWindowDimensions();
  const calendarWidth = Math.min(Math.max(width - 80, 240), 620);

  return (
    <View style={styles.container}>
      <CalendarPicker
        width={calendarWidth}
        minDate={minDate}
        selectedStartDate={value ? moment(value, 'YYYY-MM-DD') : null}
        selectedDayColor="#27899A"
        selectedDayTextColor="#FFFFFF"
        todayBackgroundColor="#E7F6F8"
        textStyle={styles.calendarText}
        onDateChange={(date) => onDateChange(date.format('YYYY-MM-DD'))}
      />
      <Text style={styles.selection}>
        {value ? moment(value, 'YYYY-MM-DD').format('MMMM D, YYYY') : 'Select a date'}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingVertical: 12,
  },
  calendarText: {
    color: '#344054',
  },
  selection: {
    width: '100%',
    maxWidth: 620,
    color: '#475467',
    fontSize: 15,
    paddingHorizontal: 8,
    paddingTop: 8,
  },
});

export default Calendar;
