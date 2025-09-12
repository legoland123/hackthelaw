from groq import Groq
import json
import os

context = """
- conflict in clauses can range from single word differences, missing clauses, or new clauses added
- For new or missing clauses, there will be no clause matched
- clauses regarding the same point may appear in the different positions for different document. 
"""

rules = """
- difference in positions should not be flagged as conflict
- clauses with conflict should be flagged out verbatim
"""

task = """
Using the examples provided above, your objective is to form a list of conflicts between clauses in document_1 and document_2. The output follows the json format in the example. For each conflict it is a list of 2 strings, with the string in the first index being from document_1, and the string in the second index being from document_2
"""

example1_doc1 = """
Termination by Notice or Payment
- After confirmation, either Party may terminate the Employment with one (1) month notice.
- The Company reserves the right, whether the Employee resigns or is dismissed, to terminate the Employment forthwith and make a payment in lieu of notice.
- On Termination Date, the Employee must return all Company property which is in his possession. The Employee will be liable to reimburse the Company for any loss of or damage to such property, except for fair wear and tear. The amount of such loss or damage shall be deducted from his final salary in the limits provided by the applicable legislation.

Termination Without Notice
- The Company may also terminate the Appointment with immediate effect without notice and with no liability to make any further payment to the Employee (other than in respect of amounts accrued due at the date of termination) if the Employee:
    - Is guilty of any gross misconduct affecting the business of the Company;
    - Is absent from work without the permission of the Company;
    - Commits any serious or repeated breach or non-observance of any of the provisions of this Agreement or refuses or neglects to comply with any reasonable and lawful directions of the Board;
    - Is, in the reasonable opinion of the Board, negligent and incompetent in the performance of his duties; or
    - Commits any fraud or dishonesty or acts in any manner which in the opinion of the Company brings or is likely to bring the Company into disrepute or is materially adverse to the interests of the Company.
    - The rights of the Company under Clause 23 are without prejudice to any other rights that it might have at law to terminate the Appointment or to accept any breach of this Agreement by the Employee as having brought the Agreement to an end. Any delay by the Company in exercising its rights to terminate shall not constitute a waiver thereof.
"""

example1_doc2 = """
Termination by Notice or Payment
- After confirmation, either Party may terminate the Employment with one (1) year notice.
- The Company reserves the right, whether the Employee resigns or is dismissed, to terminate the Employment forthwith and make a payment in lieu of notice.
- On Termination Date, the Employee can retain all Company property which are in his possession.

Termination Without Notice
- The Company may also terminate the Appointment with immediate effect without notice and with no liability to make any further payment to the Employee (other than in respect of amounts accrued due at the date of termination) if the Employee:
    - Is guilty of any gross misconduct affecting the business of the Company;
    - Drinks Coffee instead of Tea
    - Is absent from work without the permission of the Company;
    - Commits any serious or repeated breach or non-observance of any of the provisions of this Agreement or refuses or neglects to comply with any reasonable and lawful directions of the Board;
    - Is, in the reasonable opinion of the Board, negligent and incompetent in the performance of his duties; or
    - Commits any fraud or dishonesty or acts in any manner which in the opinion of the Company brings or is likely to bring the Company into disrepute or is materially adverse to the interests of the Company.
    - The rights of the Company under Clause 23 are without prejudice to any other rights that it might have at law to terminate the Appointment or to accept any breach of this Agreement by the Employee as having brought the Agreement to an end. Any delay by the Company in exercising its rights to terminate shall not constitute a waiver thereof.
"""

example1_output = "{'conflicts': [['After confirmation, either Party may terminate the Employment with one (1) month notice.', 'After confirmation, either Party may terminate the Employment with one (1) year notice.'], ['On Termination Date, the Employee must return all Company property which is in his possession. The Employee will be liable to reimburse the Company for any loss of or damage to such property, except for fair wear and tear. The amount of such loss or damage shall be deducted from his final salary in the limits provided by the applicable legislation.', 'On Termination Date, the Employee can retain all Company property which are in his possession.'], ['No clause matched', 'Drinks Coffee instead of Tea']]}"

example2_doc1 = """
Termination by Notice or Payment
- After confirmation, either Party may terminate the Employment with one (1) month notice.
- The Company reserves the right, whether the Employee resigns or is dismissed, to terminate the Employment forthwith and make a payment in lieu of notice.
- On Termination Date, the Employee must return all Company property which is in his possession. The Employee will be liable to reimburse the Company for any loss of or damage to such property, except for fair wear and tear. The amount of such loss or damage shall be deducted from his final salary in the limits provided by the applicable legislation.

Termination Without Notice
- The Company may also terminate the Appointment with immediate effect without notice and with no liability to make any further payment to the Employee (other than in respect of amounts accrued due at the date of termination) if the Employee:
    - Is guilty of any gross misconduct affecting the business of the Company;
    - Is absent from work without the permission of the Company;
    - Commits any serious or repeated breach or non-observance of any of the provisions of this Agreement or refuses or neglects to comply with any reasonable and lawful directions of the Board;
    - Is, in the reasonable opinion of the Board, negligent and incompetent in the performance of his duties; or
    - Commits any fraud or dishonesty or acts in any manner which in the opinion of the Company brings or is likely to bring the Company into disrepute or is materially adverse to the interests of the Company.
    - The rights of the Company under Clause 23 are without prejudice to any other rights that it might have at law to terminate the Appointment or to accept any breach of this Agreement by the Employee as having brought the Agreement to an end. Any delay by the Company in exercising its rights to terminate shall not constitute a waiver thereof.
"""

example2_doc2 = """
Termination by Notice or Payment
- After confirmation, either Party may terminate the Employment with one (1) month notice.
- The Company reserves the right, whether the Employee resigns or is dismissed, to terminate the Employment forthwith and make a payment in lieu of notice.
- On Termination Date, the Employee must return all Company property which is in his possession. The Employee will be liable to reimburse the Company for any loss of or damage to such property, except for fair wear and tear. The amount of such loss or damage shall be deducted from his final salary in the limits provided by the applicable legislation.

Termination Without Notice
- The Company may also terminate the Appointment with immediate effect without notice and with no liability to make any further payment to the Employee (other than in respect of amounts accrued due at the date of termination) if the Employee:
    - Is guilty of any gross misconduct affecting the business or culture of the Company;
    - Attempts to or is caught defrauding the Company card;
    - Commits any serious or repeated breach or non-observance of any of the provisions of this Agreement or refuses or neglects to comply with any reasonable and lawful directions of the Board;
    - Is, in the reasonable opinion of the Board, negligent and incompetent in the performance of his duties; or
    - Commits any fraud or dishonesty or acts in any manner which in the opinion of the Company brings or is likely to bring the Company into disrepute or is materially adverse to the interests of the Company.
    - The rights of the Company under Clause 23 are without prejudice to any other rights that it might have at law to terminate the Appointment or to accept any breach of this Agreement by the Employee as having brought the Agreement to an end. Any delay by the Company in exercising its rights to terminate shall not constitute a waiver thereof.
"""

example2_output = "{'conflicts': [['Is guilty of any gross misconduct affecting the business of the Company;', 'Is guilty of any gross misconduct affecting the business or culture of the Company;'], ['Is absent from work without the permission of the Company;', 'No clause matched'], ['No clause matched', 'Attempts to or is caught defrauding the Company card;']]}"

def main(input_doc1, input_doc2):
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY")
    )
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {
                "role": "system",
                "content": f"Context:\n{context}\n\nRules:\n{rules}"
            },
            {
                "role": "user",
                "content": f"### Example 1\ndocument_1:\n{example1_doc1}\ndocument_2:\n{example1_doc2}\noutput:\n{example1_output}\n\n### Example 2\ndocument_1:\n{example2_doc1}\ndocument_2:\n{example2_doc2}\noutput:\n{example2_output}\n\n### Task\n{task}\n\ndocuement_1:\n{input_doc1}\ndocument_2:\n{input_doc2}"
            },
        ],
        temperature=0.2,
        max_completion_tokens=4096,
        top_p=0.9,
        stream=False,
        response_format={"type": "json_object"},
        stop=None,
    )

    return json.dumps(completion.choices[0].message.content)

if __name__ == "__main__":
    input_doc1 = """
    Termination by Notice or Payment
    - After confirmation, either Party may terminate the Employment with one (1) month notice.
    - The Company reserves the right, whether the Employee resigns or is dismissed, to terminate the Employment forthwith and make a payment in lieu of notice.

    Termination Without Notice
    - The Company may also terminate the Appointment with immediate effect without notice and with no liability to make any further payment to the Employee (other than in respect of amounts accrued due at the date of termination) if the Employee:
        - Is guilty of any gross misconduct affecting the business of the Company;
        - Is absent from work without the permission of the Company;
        - Commits any serious or repeated breach or non-observance of any of the provisions of this Agreement or refuses or neglects to comply with any reasonable and lawful directions of the Board;
        - Is, in the reasonable opinion of the Board, negligent and incompetent in the performance of his duties; or
        - Commits any fraud or dishonesty or acts in any manner which in the opinion of the Company brings or is likely to bring the Company into disrepute or is materially adverse to the interests of the Company.
        - The rights of the Company under Clause 23 are without prejudice to any other rights that it might have at law to terminate the Appointment or to accept any breach of this Agreement by the Employee as having brought the Agreement to an end. Any delay by the Company in exercising its rights to terminate shall not constitute a waiver thereof.
    """
    input_doc2 = """
    Termination by Notice or Payment
    - After confirmation, either Party may terminate the Employment with one (1) month notice.
    - The Company reserves the right, whether the Employee resigns or is dismissed, to terminate the Employment forthwith and make a payment in lieu of notice.

    Termination Without Notice
    - The Company may also terminate the Appointment with immediate effect without notice and with no liability to make any further payment to the Employee (other than in respect of amounts accrued due at the date of termination) if the Employee:
        - Is guilty of any gross misconduct affecting the business or the culture of the Company;
        - Is absent from work without the permission of the Company;
        - Commits any serious or repeated breach or non-observance of any of the provisions of this Agreement or refuses or neglects to comply with any reasonable and lawful directions of the Board;
        - Commits any fraud or dishonesty or acts in any manner which in the opinion of the Company brings or is likely to bring the Company into disrepute or is materially adverse to the interests of the Company.
        - Sucks at doing his job
        - Drinks coffee over tea
    """
    main(input_doc1, input_doc2)
