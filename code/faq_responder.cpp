// faq_responder.cpp - Map categories to responses
#include "faq_responder.h"

String faqResponseForCategory(const String &cat) {
  if (cat == "requirements") {
    return F("You need to have completed 12th grade with minimum 75% marks and pass the entrance exam.");
  } else if (cat == "deadline") {
    return F("The admission deadline is March 31st, 2026.");
  } else if (cat == "fee") {
    return F("The application fee is $50 for domestic students and $100 for international students.");
  } else if (cat == "process") {
    return F("Visit our official website, create an account, fill the application form, and submit required documents.");
  } else if (cat == "documents") {
    return F("You need transcripts, ID proof, passport photo, and entrance exam scorecard.");
  } else if (cat == "greeting") {
    return F("Hello! I'm your admission assistant. How can I help you today?");
  }
  return F("I'm sorry, I didn't understand your question. Please ask about admissions, requirements, deadlines, fees, or application process.");
}
