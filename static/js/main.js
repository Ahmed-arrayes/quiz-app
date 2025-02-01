// Check quiz answer
function checkAnswer(questionId, answer) {
    const startTime = new Date().getTime();
    
    $.ajax({
        url: '/api/quiz-feedback',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            question_id: questionId,
            answer: answer,
            time_taken: (new Date().getTime() - startTime) / 1000
        }),
        success: function(response) {
            const feedbackContainer = $('#feedback-container');
            const feedbackAlert = feedbackContainer.find('.alert');
            
            feedbackAlert.removeClass('alert-success alert-danger')
                        .addClass(response.is_correct ? 'alert-success' : 'alert-danger');
            
            $('#feedback-title').text(response.is_correct ? 'أحسنت!' : 'حاول مرة أخرى');
            $('#feedback-text').html(response.feedback);
            $('#explanation-text').html(response.explanation);
            
            feedbackContainer.show();
        }
    });
}

// Updating study tips
function updateStudyTips(category, topic) {
    $.ajax({
        url: '/api/start-quiz',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            category: category,
            topic: topic
        }),
        success: function(response) {
            $('#study-tips').html(response.study_tip);
        }
    });
}

// Remaining time update
function updateTimer() {
    const timeLeft = getTimeRemaining();
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    
    $('#timer').text(`${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`);
    
    if (timeLeft <= 300 && timeLeft % 60 === 0) {  // Update every minute in the last 5 minutes
        updateProgress(currentQuestion, totalQuestions);
    }
}

// Starting the quiz
function startQuiz(event) {
    event.preventDefault();
    console.log('Starting quiz...');
    
    const form = event.target;
    const formData = {
        subject: form.querySelector('[name="subject"]').value,
        topic: form.querySelector('[name="topic"]').value,
        question_count: parseInt(form.querySelector('[name="question_count"]').value)
    };
    
    console.log('Form data:', formData);

    $.ajax({
        url: '/api/start-quiz',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            console.log('Success:', response);
            if (response.redirect) {
                window.location.href = response.redirect;
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
            console.error('Status:', status);
            console.error('Response:', xhr.responseText);
            alert('حدث خطأ أثناء بدء الاختبار. الرجاء المحاولة مرة أخرى.');
        }
    });
}

// When the page loads
$(document).ready(function() {
    console.log('Document ready');
    // Update study tips at quiz start
    const category = $('#quiz-form').data('category');
    const topic = $('#quiz-form').data('topic');
    updateStudyTips(category, topic);

    // Handling answers
    $('input[name="answer"]').change(function() {
        const questionId = $(this).closest('.question-card').data('question-id');
        checkAnswer(questionId, $(this).val());
    });

    // Update progress and time
    setInterval(updateTimer, 1000);

    // Adding event listener to start quiz form
    const quizForm = document.getElementById('quiz-form');
    console.log('Quiz form:', quizForm);
    
    if (quizForm) {
        quizForm.addEventListener('submit', startQuiz);
        console.log('Added submit event listener');
    }
});